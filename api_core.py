# api_core.py
import database_manager
from analytics import AnalyticsManager
from datetime import date

# Inicializa os gerenciadores globais
DB_MANAGER = database_manager.DatabaseManager()
ANALYTICS_MANAGER = AnalyticsManager()

# --- AUTENTICAÇÃO E USUÁRIOS ---

def verify_login_web(username, password):
    """Verifica login e retorna o user_id se for sucesso, ou None."""
    return DB_MANAGER.verify_login(username, password)

def register_user_web(username, password):
    """Tenta registrar novo usuário. Retorna True/False."""
    if not username or not password:
         return False
    return DB_MANAGER.register_user(username, password)

# --- LOGS E DADOS ---

def get_config_for_display(user_id):
    """Retorna as configurações do usuário no formato de display (Semanal e Diário)."""
    # Recarrega a config para garantir que é a mais recente
    ANALYTICS_MANAGER.config = ANALYTICS_MANAGER._load_config() 
    
    current_config = ANALYTICS_MANAGER.config
    current_consumo = current_config.get('VEICULO', {}).get('CONSUMO_MEDIO_KM_L', 0.0)
    current_preco = current_config.get('CUSTOS', {}).get('PRECO_COMBUSTIVEL_L', 0.0)
    current_tipo = current_config.get('VEICULO', {}).get('TIPO_COMBUSTIVEL', 'N/A')
    current_fixed_daily = current_config.get('CUSTOS', {}).get('CUSTO_FIXO_DIARIO', 0.0)
    
    # Converte o valor diário para semanal para exibir
    current_fixed_weekly = round(current_fixed_daily * 7, 2)

    return {
        "consumo": current_consumo,
        "preco": current_preco,
        "tipo": current_tipo,
        "fixo_semanal": current_fixed_weekly,
        "fixo_diario": current_fixed_daily
    }


def update_config_web(consumo, preco, tipo, aluguel_semanal):
    """Atualiza as configurações e salva no JSON."""
    
    # 1. Trata o valor de Custo Fixo Semanal para Diário
    fixed_daily_cost = round(aluguel_semanal / 7, 2) if aluguel_semanal > 0 else 0.0
    
    # 2. Lógica para carro Elétrico
    new_consumo = consumo
    new_preco = preco
    
    if tipo.upper() in ('ELÉTRICO', 'ELETRICO'):
        new_consumo = 0.0
        new_preco = 0.0
        
    # 3. Salva no config.json (aqui chamamos o método do AnalyticsManager)
    return ANALYTICS_MANAGER._save_config(
        new_consumo, new_preco, tipo, fixed_daily_cost
    )

def upsert_log_web(user_id, data, km_rodados, faturamento_total, horas_trabalhadas):
    """Insere/Atualiza log e retorna o resumo de métricas do dia."""
    
    # 1. Salva/Atualiza no BD
    if not DB_MANAGER.upsert_daily_log(user_id, data, km_rodados, faturamento_total, horas_trabalhadas):
        return None
    
    # 2. Calcula e retorna as métricas
    metrics = ANALYTICS_MANAGER.calculate_performance_metrics(
        km_rodados, faturamento_total, horas_trabalhadas
    )
    
    # Inclui os dados brutos
    return {
        "km": km_rodados,
        "fat": faturamento_total,
        "horas": horas_trabalhadas,
        **metrics
    }

def get_report_web(user_id):
    """Busca todos os logs, calcula as métricas diárias e gerais, e retorna tudo em um dicionário."""
    
    all_logs = DB_MANAGER.get_all_logs_by_user(user_id)
    if not all_logs:
        return {"logs_diarios": [], "geral": None}
    
    # 1. Logs diários com métricas
    daily_logs_with_metrics = []
    for log in all_logs:
        data, km, fat, hrs = log
        daily_metrics = ANALYTICS_MANAGER.calculate_performance_metrics(km, fat, hrs)
        
        daily_logs_with_metrics.append({
            "data": data,
            "km": km,
            "fat": fat,
            "custo_comb": daily_metrics['custo_combustivel_estimado'],
            "lucro_liquido": daily_metrics['lucro_liquido'],
            "horas": hrs
        })
        
    # 2. Totais gerais
    overall_metrics = ANALYTICS_MANAGER.calculate_overall_metrics(all_logs)

    # 3. Cálculo do Lucro Líquido TOTAL
    fixed_daily_cost = ANALYTICS_MANAGER.config.get('CUSTOS', {}).get('CUSTO_FIXO_DIARIO', 0.0)
    fixed_cost_total = overall_metrics['total_dias'] * fixed_daily_cost
    total_lucro_liquido = overall_metrics['total_faturamento'] - overall_metrics['custo_total_estimado'] - fixed_cost_total
    
    overall_metrics['custo_fixo_total'] = fixed_cost_total
    overall_metrics['total_lucro_liquido'] = total_lucro_liquido
    
    return {
        "logs_diarios": daily_logs_with_metrics,
        "geral": overall_metrics
    }