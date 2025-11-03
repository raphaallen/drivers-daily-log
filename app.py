import database_manager
from analytics import AnalyticsManager
from datetime import date, datetime # Importado datetime para validação de data
import sys 

# Inicializa os gerenciadores no escopo global
DB_MANAGER = database_manager.DatabaseManager()
ANALYTICS_MANAGER = AnalyticsManager()

# Variável global para armazenar o ID do usuário logado
LOGGED_IN_USER_ID = None 


# --- CONSTANTES DE INFORMAÇÃO ---
INSTRUCTION_POPUP = """
\n--- 💡 INSTRUÇÕES DE CONSUMO MÉDIO ---
Se você não souber o consumo médio (Km/L) do seu veículo:
1. Anote a quilometragem atual.
2. Abasteça o tanque COMPLETAMENTE.
3. Zere o hodômetro parcial e use o carro até o próximo abastecimento.
4. Anote quantos litros foram necessários para encher o tanque COMPLETAMENTE de novo.
5. Fórmula: (KM rodados no período) / (Litros abastecidos) = Km/L.
Exemplo: 350 Km / 35 Litros = 10 Km/L.
--------------------------------------
"""


# --- FUNÇÕES UTILITÁRIAS ---
def get_valid_input(prompt, data_type=float):
    """
    Pede uma entrada ao usuário e garante que ela é do tipo esperado.
    """
    while True:
        try:
            value = input(prompt).replace(',', '.') # Substitui vírgula por ponto
            if not value and data_type == str:
                return ""
            if data_type == float:
                return float(value)
            elif data_type == str:
                return value
            return value
        except ValueError:
            print("❌ Erro: Entrada inválida. Por favor, digite apenas números válidos (ex: 275.50 ou 8.0).")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            sys.exit(1)


# --- FUNÇÕES DE LOGIN/CADASTRO ---

def register_user_flow():
    """Fluxo para cadastro de um novo usuário."""
    print("\n--- 📝 Novo Cadastro ---")
    username = input("Novo Usuário: ")
    password = input("Nova Senha: ")
    if not username or not password:
         print("❌ Usuário e senha não podem ser vazios.")
         return False
    
    if DB_MANAGER.register_user(username, password):
        print("✅ Cadastro realizado com sucesso! Faça login para continuar.")
    else:
        print("❌ Falha no cadastro. O nome de usuário pode já existir.")
    return False 


def login_menu():
    """Exibe o menu de login/cadastro e define o usuário logado."""
    global LOGGED_IN_USER_ID
    
    print("\n--- 🔐 Login / Cadastro ---")
    print("1. Entrar (Login)")
    print("2. Novo Usuário (Cadastrar)")
    print("3. ❌ Sair do Sistema")
    choice = input("Escolha uma opção (1-3): ")
    
    if choice == '1':
        username = input("Usuário: ")
        password = input("Senha: ")
        user_id = DB_MANAGER.verify_login(username, password)
        if user_id:
            LOGGED_IN_USER_ID = user_id
            print(f"🎉 Login bem-sucedido! Bem-vindo(a), {username}!")
            return True
        else:
            print("❌ Usuário ou senha inválidos.")
            return False
    
    elif choice == '2':
        register_user_flow()
        return False 
        
    elif choice == '3':
        print("👋 Encerrando o sistema. Até logo!")
        sys.exit(0)
    
    return False

# --- FUNÇÕES PRINCIPAIS DE GESTÃO ---

def register_daily_log_upsert():
    """Coleta dados do usuário (total acumulado) para o dia especificado e atualiza/insere."""
    global LOGGED_IN_USER_ID
    user_id = LOGGED_IN_USER_ID
    
    # 1. COLETAR A DATA (Default: Hoje)
    hoje = date.today().isoformat()
    while True:
        # Pede a data, aceita Enter para o dia de hoje
        data_input = input(f"\nData do Log (AAAA-MM-DD, ou Enter para HOJE: {hoje}): ") or hoje
        try:
            # Validação simples do formato AAAA-MM-DD
            datetime.strptime(data_input, '%Y-%m-%d')
            target_date = data_input
            break
        except ValueError:
            print("❌ Formato de data inválido. Use AAAA-MM-DD (Ex: 2024-03-15).")
            continue
            
    # 2. Busca os dados existentes para dar um contexto ao usuário
    existing_log = DB_MANAGER.get_daily_log(user_id, target_date) 
    
    if existing_log:
        km_atual, fat_atual, hrs_atual = existing_log
        print(f"\n--- 🔄 Atualizando Log do Dia: {target_date} ---")
        print(f"Dados ATUAIS registrados: {km_atual:.2f} KM, R${fat_atual:.2f}, {hrs_atual:.2f} Horas")
        print(">> Insira os VALORES TOTAIS ACUMULADOS para o dia:")
    else:
        print(f"\n--- 📝 Novo Log do Dia: {target_date} ---")
        
    # 3. Coleta os dados (os valores TOTAIS do dia até o momento)
    km_rodados_total = get_valid_input("TOTAL de KM Rodados nesse dia: ")
    faturamento_total = get_valid_input("TOTAL Faturado (R$) nesse dia: ")
    horas_trabalhadas_total = get_valid_input("TOTAL de Horas Trabalhadas nesse dia: ")
    
    # 4. Executa o UPSERT (Atualiza ou Insere)
    if DB_MANAGER.upsert_daily_log(user_id, target_date, km_rodados_total, faturamento_total, horas_trabalhadas_total):
        
        # 5. Realiza e exibe a Análise CONSOLIDADA dos novos totais
        print(f"\n--- 📊 Resumo e Análise do Dia {target_date} ---")
        
        metrics = ANALYTICS_MANAGER.calculate_performance_metrics(
            km_rodados_total, faturamento_total, horas_trabalhadas_total
        )
        
        print(f"KM Total do Dia: {km_rodados_total:.2f} km")
        print(f"Faturamento Total Bruto: R${faturamento_total:.2f}")
        print(f"Horas Totais: {horas_trabalhadas_total:.2f} h")
        print("-" * 30)
        print(f"💰 Reais por Km: R${metrics['reais_por_km']:.2f}")
        print(f"⏰ Reais por Hora Bruta: R${metrics['reais_por_hora']:.2f}")
        print(f"💲 Custo de Combustível Estimado: R${metrics['custo_combustivel_estimado']:.2f}")
        print("-" * 30)
        # LUCRO LÍQUIDO
        print(f"✨ LUCRO LÍQUIDO NO DIA: R${metrics['lucro_liquido']:.2f} ✨")
    
    print("-" * 50)


def config_menu_flow():
    """Permite ao usuário editar as configurações de combustível e custos fixos."""
    print("\n--- ⚙️ Configurações de Custos e Consumo ---")
    
    # Exibir as configurações atuais
    current_config = ANALYTICS_MANAGER.config
    current_consumo = current_config.get('VEICULO', {}).get('CONSUMO_MEDIO_KM_L', 0.0)
    current_preco = current_config.get('CUSTOS', {}).get('PRECO_COMBUSTIVEL_L', 0.0)
    current_tipo = current_config.get('VEICULO', {}).get('TIPO_COMBUSTIVEL', 'N/A')
    
    # NOVO: Tentativa de converter custo fixo diário para semanal para exibir
    current_fixed_daily = current_config.get('CUSTOS', {}).get('CUSTO_FIXO_DIARIO', 0.0)
    current_fixed_weekly = round(current_fixed_daily * 7, 2)

    print(f"\n[Valores Atuais]")
    print(f"Tipo de Combustível: {current_tipo}")
    print(f"Média de Consumo (Km/L): {current_consumo}")
    print(f"Preço do Combustível (R$/L): R${current_preco}")
    print(f"Custo Fixo SEMANAL (Aluguel/Taxa): R${current_fixed_weekly:.2f}")
    print("-" * 35)

    # 1. NOVO CUSTO FIXO (Aluguel Semanal -> Diário)
    print("\n--- 💸 CUSTO FIXO SEMANAL (Aluguel, Financiamento, Taxas) ---")
    print("Digite 0 se for carro próprio ou não houver custo fixo semanal.")
    new_aluguel_semanal = get_valid_input(f"Novo Custo Fixo SEMANAL (Atual: R${current_fixed_weekly:.2f}): ", data_type=float)
    
    # Conversão para o valor diário que será usado nos cálculos (Divisão por 7)
    new_fixed_daily_cost = round(new_aluguel_semanal / 7, 2) if new_aluguel_semanal > 0 else 0.0
    print(f"✅ Custo Fixo Diário calculado: R${new_fixed_daily_cost:.2f}")
    print("-" * 35)


    # 2. CONFIGURAÇÃO DE COMBUSTÍVEL E INSTRUÇÕES
    print("\n--- ⛽ Configuração de Combustível ---")
    print("Opções: Gasolina, Etanol, Diesel, Elétrico (Ou qualquer string)")
    new_type = input(f"Novo Tipo de Combustível (Atual: {current_tipo}): ") or current_tipo
    
    
    # Variáveis default caso o carro seja Elétrico ou a pessoa deixe vazio
    new_consumo = current_consumo
    new_preco = current_preco

    if new_type.upper() in ('ELÉTRICO', 'ELETRICO'):
        print("\nℹ️  Carro Elétrico selecionado. O cálculo de combustível (Km/L e Preço) será zerado.")
        new_consumo = 0.0
        new_preco = 0.0
    else:
        # Instrução apenas para quem precisa calcular Km/L
        print(INSTRUCTION_POPUP)
        new_consumo = get_valid_input(f"Nova Média de Consumo (Km/L) (Atual: {current_consumo}): ", data_type=float)
        new_preco = get_valid_input(f"Novo Preço do Combustível (R$/L) (Atual: {current_preco}): ", data_type=float)


    # 3. Salvar as configurações (Passando o custo DIÁRIO)
    if ANALYTICS_MANAGER._save_config(new_consumo, new_preco, new_type, new_fixed_daily_cost):
        print("\n✅ Configurações atualizadas com sucesso!")
    else:
        print("\n❌ Falha ao salvar as configurações.")

    print("-" * 50)


def display_full_report():
    """Busca todos os logs do usuário logado e exibe o relatório e as médias, incluindo Lucro Líquido."""
    global LOGGED_IN_USER_ID
    user_id = LOGGED_IN_USER_ID
    
    print("\n--- 📑 Relatório Completo de Logs ---")
    
    # 1. Busca os logs
    all_logs = DB_MANAGER.get_all_logs_by_user(user_id)
    
    if not all_logs:
        print("Nenhum registro de log encontrado. Comece registrando seu primeiro dia!")
        print("-" * 50)
        return

    # 2. Exibir Logs Individuais (Tabela simples com Lucro Líquido)
    print(f"| {'Data':<12} | {'KM':<6} | {'Fat. Bruto':<12} | {'Custo Comb':<12} | {'Lucro Líquido':<15} | {'Horas':<6} |")
    print("-" * 76)
    
    # Recalcula as métricas para cada log para exibir o Lucro Líquido
    for log in all_logs:
        data, km, fat, hrs = log
        daily_metrics = ANALYTICS_MANAGER.calculate_performance_metrics(km, fat, hrs)
        
        lucro_liquido = daily_metrics['lucro_liquido']
        custo_comb = daily_metrics['custo_combustivel_estimado']
        
        # Apenas arredondamos KM e Horas para o print, os dados brutos são REAIS
        print(f"| {data:<12} | {km:<6.0f} | {fat:<12.2f} | {custo_comb:<12.2f} | {lucro_liquido:<15.2f} | {hrs:<6.1f} |")
    print("-" * 76)
    
    # 3. Calcular e Exibir Médias Gerais
    overall_metrics = ANALYTICS_MANAGER.calculate_overall_metrics(all_logs)

    if overall_metrics:
        # Custo Fixo Diário (Recupera para o cálculo total)
        fixed_daily_cost = ANALYTICS_MANAGER.config.get('CUSTOS', {}).get('CUSTO_FIXO_DIARIO', 0.0)
        fixed_cost_total = overall_metrics['total_dias'] * fixed_daily_cost
        
        # CÁLCULO GERAL DE LUCRO LÍQUIDO
        total_lucro_liquido = overall_metrics['total_faturamento'] - overall_metrics['custo_total_estimado'] - fixed_cost_total
        
        print("\n--- 📈 Totais e Médias Gerais ---")
        print(f"🗓️ Total de Dias Registrados: {overall_metrics['total_dias']}")
        print(f"🛣️ KM Total Rodado: {overall_metrics['total_km']:.2f} km")
        print(f"💰 Faturamento Total Bruto: R${overall_metrics['total_faturamento']:.2f}")
        print(f"💲 Custo Total de Combustível Estimado: R${overall_metrics['custo_total_estimado']:.2f}")
        print(f"💵 Custo Fixo Total (Aluguel/Taxa): R${fixed_cost_total:.2f}")
        print(f"**✨ LUCRO LÍQUIDO TOTAL: R${total_lucro_liquido:.2f} ✨**")
        print("-" * 40)
        print(f"KM Médio por Dia: {overall_metrics['km_medio_dia']:.2f} km")
        print(f"R$/KM Médio GERAL (Bruto): R${overall_metrics['reais_por_km_medio']:.2f}")
        print(f"R$/HORA Média GERAL (Bruta): R${overall_metrics['reais_por_hora_medio']:.2f}")

    print("-" * 50)


# --- FLUXO PRINCIPAL E MENUS ---

def display_menu():
    """Exibe o menu principal (Após o login)."""
    print("\n--- 🚗 Driver's Daily Log Menu ---")
    print("1. 📝 Registrar/Atualizar Log (Data Flexível)")
    print("2. 📑 Visualizar Todos os Logs e Relatório Geral")
    print("3. ⚙️ Configurações de Custos") 
    print("4. ❌ Logout") 
    
    choice = get_valid_input("Escolha uma opção (1-4): ", data_type=str) 
    return choice

def main():
    """Função principal que gerencia o fluxo da aplicação."""
    print("--- 🚗 Driver's Daily Log - Sistema de Gerenciamento ---")

    global LOGGED_IN_USER_ID

    # Loop de autenticação inicial
    while not LOGGED_IN_USER_ID:
        login_menu()

    # Loop principal do aplicativo (só roda se estiver logado)
    while LOGGED_IN_USER_ID:
        choice = display_menu()
        
        if choice == '1':
            register_daily_log_upsert()
        elif choice == '2':
            display_full_report()
        elif choice == '3':
            config_menu_flow() 
        elif choice == '4': 
            print(f"👋 Usuário {LOGGED_IN_USER_ID} desconectado.")
            LOGGED_IN_USER_ID = None 
            while not LOGGED_IN_USER_ID:
                login_menu()
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    # Garante que as tabelas existem antes de qualquer operação
    DB_MANAGER._connect() 
    DB_MANAGER._disconnect()
    main()