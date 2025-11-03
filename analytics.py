import json
import os
import sqlite3

# Caminho para o arquivo de configuração
CONFIG_FILE = 'config.json'

class AnalyticsManager:
    """
    Responsável por carregar configurações e realizar todos os cálculos de 
    desempenho e custos baseados nos dados brutos do log diário.
    """
    
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self):
        """Carrega e retorna os dados do arquivo config.json."""
        if not os.path.exists(CONFIG_FILE):
            print(f"ERRO: Arquivo de configuração '{CONFIG_FILE}' não encontrado.")
            return {}
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERRO: Formato inválido no arquivo JSON: {e}")
            return {}
        except KeyError:
            # Garante que as chaves de topo existam, mesmo que vazias
            return {'VEICULO': {}, 'CUSTOS': {}}
        
    
    def _save_config(self, new_consumption, new_price, new_type, new_fixed_daily_cost):
        """Salva as novas configurações de combustível e custos fixos diários no config.json."""
        # Se as chaves VEICULO ou CUSTOS não existirem, cria
        if 'VEICULO' not in self.config: self.config['VEICULO'] = {}
        if 'CUSTOS' not in self.config: self.config['CUSTOS'] = {}

        self.config['VEICULO']['CONSUMO_MEDIO_KM_L'] = new_consumption
        self.config['VEICULO']['TIPO_COMBUSTIVEL'] = new_type
        self.config['CUSTOS']['PRECO_COMBUSTIVEL_L'] = new_price
        self.config['CUSTOS']['CUSTO_FIXO_DIARIO'] = new_fixed_daily_cost 
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            self.config = self._load_config()
            return True
        except Exception as e:
            print(f"ERRO ao salvar as configurações no JSON: {e}")
            return False

    # --- FUNÇÕES DE CÁLCULO DENTRO DA CLASSE ---

    def calculate_performance_metrics(self, km_rodados, faturamento_total, horas_trabalhadas):
        """
        Calcula as métricas de performance e o Lucro Líquido Real (subtraindo Combustível e Custo Fixo Diário).
        """
        metrics = {
            "reais_por_km": 0.0,
            "reais_por_hora": 0.0,
            "custo_combustivel_estimado": 0.0,
            "litros_gastos": 0.0,
            "lucro_liquido": 0.0 
        }

        # 1. Obter dados de configuração
        # Usamos 0.0 como default para garantir que não haja divisão por zero
        consumo_km_l = self.config.get('VEICULO', {}).get('CONSUMO_MEDIO_KM_L', 0.0)
        preco_combustivel = self.config.get('CUSTOS', {}).get('PRECO_COMBUSTIVEL_L', 0.0)
        custo_fixo_diario = self.config.get('CUSTOS', {}).get('CUSTO_FIXO_DIARIO', 0.0) 
        tipo_combustivel = self.config.get('VEICULO', {}).get('TIPO_COMBUSTIVEL', 'N/A')

        # 2. Reais por Km e Reais por Hora (Cálculo Básico)
        if km_rodados > 0:
            metrics["reais_por_km"] = round(faturamento_total / km_rodados, 2)
        if horas_trabalhadas > 0:
            metrics["reais_por_hora"] = round(faturamento_total / horas_trabalhadas, 2)

        # 3. Custo Estimado de Combustível (Condicional para Elétrico)
        if tipo_combustivel.upper() not in ('ELÉTRICO', 'ELETRICO'):
            if km_rodados > 0 and consumo_km_l > 0:
                metrics["litros_gastos"] = km_rodados / consumo_km_l
                metrics["custo_combustivel_estimado"] = round(metrics["litros_gastos"] * preco_combustivel, 2)
        else:
            # Para carro elétrico, o custo de "combustível" é zero.
            metrics["custo_combustivel_estimado"] = 0.0
            
        # 4. LUCRO LÍQUIDO REAL
        metrics["lucro_liquido"] = round(faturamento_total - metrics["custo_combustivel_estimado"] - custo_fixo_diario, 2)

        return metrics
    
    def calculate_overall_metrics(self, all_logs):
        """
        Calcula os totais e as métricas médias de performance de todos os logs fornecidos.
        Retorna um dicionário com os resultados.
        """
        if not all_logs:
            return None

        # log[1] = km_rodados, log[2] = faturamento_total, log[3] = horas_trabalhadas
        total_km = sum(log[1] for log in all_logs)
        total_faturamento = sum(log[2] for log in all_logs)
        total_horas = sum(log[3] for log in all_logs)
        num_dias = len(all_logs)

        metrics = {
            "total_dias": num_dias,
            "total_km": round(total_km, 2),
            "total_faturamento": round(total_faturamento, 2),
            "total_horas": round(total_horas, 2),
            "km_medio_dia": round(total_km / num_dias, 2) if num_dias > 0 else 0.0
        }

        # Reutiliza a função calculate_performance_metrics para calcular as médias GERAIS
        overall_performance = self.calculate_performance_metrics(
            total_km, total_faturamento, total_horas
        )
        
        # O resultado será Reais/Km GERAL e Custo Estimado GERAL
        metrics["reais_por_km_medio"] = overall_performance["reais_por_km"]
        metrics["reais_por_hora_medio"] = overall_performance["reais_por_hora"]
        metrics["custo_total_estimado"] = overall_performance["custo_combustivel_estimado"]

        return metrics