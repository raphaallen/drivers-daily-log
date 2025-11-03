# web_app.py
import streamlit as st
import pandas as pd
from datetime import date
# Importamos a nossa camada de lógica que acabamos de criar
import api_core as core 

# --- CONFIGURAÇÕES BÁSICAS DO STREAMLIT ---
st.set_page_config(
    page_title="Driver's Daily Log - V0.1 Web",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GERENCIAMENTO DE SESSÃO ---
# O Streamlit usa st.session_state para armazenar variáveis entre as interações
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'


# --- FUNÇÕES DE NAVEGAÇÃO ---
def set_page(page_name):
    st.session_state.page = page_name

def navigate_to_app():
    st.session_state.logged_in = True
    st.session_state.page = 'register' # Começa na página de Registro

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.page = 'login'
    st.rerun()


# --- FUNÇÕES DE RENDERIZAÇÃO DE PÁGINAS ---

# 1. PÁGINA DE LOGIN
def render_login_page():
    st.title("Driver's Daily Log 🚗")
    st.header("Login / Cadastro")

    # Colunas para organizar o formulário
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Entrar")
        login_form = st.form(key='login_form')
        login_username = login_form.text_input("Usuário", key='l_user')
        login_password = login_form.text_input("Senha", type="password", key='l_pass')
        login_submit = login_form.form_submit_button("Entrar no Sistema")

        if login_submit:
            user_id = core.verify_login_web(login_username, login_password)
            if user_id:
                st.session_state.user_id = user_id
                navigate_to_app()
                st.success(f"Login bem-sucedido! Bem-vindo(a), {login_username}!")
            else:
                st.error("Usuário ou senha inválidos.")

    with col2:
        st.subheader("Novo Cadastro")
        register_form = st.form(key='register_form')
        reg_username = register_form.text_input("Novo Usuário", key='r_user')
        reg_password = register_form.text_input("Nova Senha", type="password", key='r_pass')
        register_submit = register_form.form_submit_button("Cadastrar")

        if register_submit:
            if core.register_user_web(reg_username, reg_password):
                st.success("✅ Cadastro realizado com sucesso! Faça login ao lado.")
            else:
                st.error("❌ Falha no cadastro. Usuário pode já existir ou campos estão vazios.")

# 2. PÁGINA DE REGISTRO
def render_register_log_page():
    st.header("📝 Registrar/Atualizar Log")
    
    with st.form("log_form"):
        # Data do Log (usa o widget de data nativo)
        data_log = st.date_input("Data do Log", value=date.today())
        
        # Campos de entrada de dados
        km_rodados = st.number_input("TOTAL de KM Rodados nesse dia", min_value=0.0, format="%.2f", step=1.0)
        faturamento_total = st.number_input("TOTAL Faturado (R$) nesse dia", min_value=0.0, format="%.2f", step=1.0)
        horas_trabalhadas = st.number_input("TOTAL de Horas Trabalhadas nesse dia", min_value=0.0, max_value=24.0, format="%.2f", step=0.1)
        
        submitted = st.form_submit_button("Salvar Log e Calcular Desempenho")

        if submitted:
            # Chama a função do nosso Backend (api_core)
            metrics = core.upsert_log_web(
                st.session_state.user_id, 
                data_log.isoformat(), 
                km_rodados, 
                faturamento_total, 
                horas_trabalhadas
            )
            
            if metrics:
                st.success(f"✅ Log do dia {data_log.strftime('%d/%m/%Y')} salvo e calculado!")
                st.subheader("📊 Resumo e Análise do Dia")
                
                # Exibe o resumo das métricas (AGORA NO WEB!)
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("💰 Reais por Km", f"R${metrics['reais_por_km']:.2f}")
                col_m2.metric("⏰ Reais por Hora Bruta", f"R${metrics['reais_por_hora']:.2f}")
                col_m3.metric("💲 Custo Comb. Estimado", f"R${metrics['custo_combustivel_estimado']:.2f}")
                
                # Destaca o Lucro Líquido Real
                st.markdown(f"### ✨ LUCRO LÍQUIDO NO DIA: R$ {metrics['lucro_liquido']:.2f} ✨")
            else:
                st.error("❌ Falha ao salvar ou calcular o log.")


# 3. PÁGINA DE RELATÓRIO
def render_full_report_page():
    st.header("📑 Relatório Completo de Logs")
    
    # Chama a função do nosso Backend
    report = core.get_report_web(st.session_state.user_id)
    
    if not report['logs_diarios']:
        st.info("Nenhum registro de log encontrado. Comece registrando seu primeiro dia!")
        return

    st.subheader("📈 Totais e Médias Gerais")
    
    geral = report['geral']
    
    # Exibe os totais com formatação
    col_g1, col_g2, col_g3 = st.columns(3)
    col_g1.metric("Dias Registrados", geral['total_dias'])
    col_g2.metric("KM Total Rodado", f"{geral['total_km']:.2f} km")
    col_g3.metric("Faturamento Bruto Total", f"R$ {geral['total_faturamento']:.2f}")

    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("Custo Comb. Total", f"R$ {geral['custo_total_estimado']:.2f}")
    col_c2.metric("Custo Fixo Total", f"R$ {geral['custo_fixo_total']:.2f}")
    
    # Destaque para o Lucro Líquido
    col_c3.metric("LUCRO LÍQUIDO TOTAL", f"R$ {geral['total_lucro_liquido']:.2f}")

    # Médias de Performance
    st.markdown("---")
    st.subheader("Médias de Desempenho")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("R$/KM Médio GERAL (Bruto)", f"R$ {geral['reais_por_km_medio']:.2f}")
    col_m2.metric("R$/HORA Média GERAL (Bruta)", f"R$ {geral['reais_por_hora_medio']:.2f}")


    st.markdown("---")
    st.subheader("Detalhes Diários")
    
    # Cria um DataFrame do Pandas para exibir a tabela bonita
    df = pd.DataFrame(report['logs_diarios'])
    # Renomeia colunas para o português
    df.columns = ['Data', 'KM', 'Faturamento Bruto', 'Custo Combustível', 'Lucro Líquido', 'Horas']
    
    st.dataframe(df, use_container_width=True)


# 4. PÁGINA DE CONFIGURAÇÕES
def render_config_page():
    st.header("⚙️ Configurações de Custos e Consumo")
    
    # 1. Busca as configurações atuais para preencher o formulário
    current_config = core.get_config_for_display(st.session_state.user_id)
    
    st.subheader("Valores Atuais")
    col_curr1, col_curr2 = st.columns(2)
    col_curr1.info(f"Tipo: **{current_config['tipo']}** | Consumo: **{current_config['consumo']} Km/L**")
    col_curr2.info(f"Custo Semanal: **R$ {current_config['fixo_semanal']:.2f}** | Diário: **R$ {current_config['fixo_diario']:.2f}**")
    
    
    st.markdown("---")
    st.subheader("Atualizar Configurações")
    
    with st.form("config_form"):
        st.markdown("#### ⛽ Combustível")
        col_c1, col_c2, col_c3 = st.columns(3)
        
        tipos_combustivel = ['Gasolina', 'Etanol', 'Diesel', 'Elétrico', 'Outro']
        new_tipo = col_c1.selectbox("Tipo de Combustível", tipos_combustivel, index=tipos_combustivel.index(current_config['tipo']) if current_config['tipo'] in tipos_combustivel else 4)
        
        # Ajusta inputs baseados no tipo (para Elétrico, o consumo e preço são ignorados, mas para fins de UI, deixamos como está)
        new_consumo = col_c2.number_input("Média de Consumo (Km/L)", min_value=0.0, value=current_config['consumo'], format="%.2f", step=0.1)
        new_preco = col_c3.number_input("Preço do Combustível (R$/L)", min_value=0.0, value=current_config['preco'], format="%.2f", step=0.01)

        st.markdown("#### 💸 Custo Fixo Semanal")
        new_aluguel_semanal = st.number_input("Custo Fixo SEMANAL (Aluguel, Taxas, etc.) - Digite 0 se for carro próprio.", min_value=0.0, value=current_config['fixo_semanal'], format="%.2f", step=1.0)
        
        submitted = st.form_submit_button("Salvar Configurações")
        
        if submitted:
            if core.update_config_web(new_consumo, new_preco, new_tipo, new_aluguel_semanal):
                st.success(f"✅ Configurações atualizadas! Custo Diário Calculado: R$ {new_aluguel_semanal/7:.2f}")
                st.session_state.page = 'config' # Força recarregar a página para mostrar os novos valores
                st.rerun()
            else:
                st.error("❌ Falha ao salvar as configurações.")


# --- FUNÇÃO PRINCIPAL ---
def main_web_app():
    """Gerencia a navegação e o layout do aplicativo."""

    # Se não estiver logado, sempre mostra o login
    if not st.session_state.logged_in:
        render_login_page()
        return

    # Se estiver logado, monta a barra lateral (Sidebar) e o menu
    with st.sidebar:
        st.title(f"Olá, User {st.session_state.user_id}")
        st.button("📝 Novo Log", on_click=set_page, args=['register'])
        st.button("📑 Relatório Geral", on_click=set_page, args=['report'])
        st.button("⚙️ Configurações", on_click=set_page, args=['config'])
        st.markdown("---")
        st.button("❌ Logout", on_click=logout)
        st.markdown("---")
        st.caption("Desenvolvido para portfólio de Fullstack Python")

    # Renderiza a página principal
    if st.session_state.page == 'register':
        render_register_log_page()
    elif st.session_state.page == 'report':
        render_full_report_page()
    elif st.session_state.page == 'config':
        render_config_page()
    else:
        render_register_log_page() # Default

# Garante que o DB está pronto antes de tudo (como fazíamos no main do app.py)
DB_MANAGER = core.DB_MANAGER
DB_MANAGER._connect() 
DB_MANAGER._disconnect()

if __name__ == "__main__":
    main_web_app()