# 🚗 Driver's Daily Log: Core de Análise de Performance para Motoristas (Fullstack Python)

Este projeto representa o **Core Backend** e a **Prova de Conceito (PoC) Web** para uma ferramenta essencial de gestão financeira e de performance para motoristas de aplicativo e logística. O objetivo foi criar uma arquitetura robusta e escalável, focada em fornecer métricas de lucro líquido real e custo operacional.

## 🌟 Nossa Contribuição: A Engenharia por Trás da Análise

Nossa equipe foi responsável por toda a **Arquitetura de Backend** e pela **Camada de Dados (Database Layer)** do projeto, garantindo que o Frontend (atualmente em desenvolvimento por outra equipe) receba dados limpos e métricas de alto valor.

### 1. Desafios de Engenharia Solucionados

* **Lógica de Negócio Criteriosa (`analytics.py`):** Desenvolvimento de algoritmos para calcular o **Lucro Líquido Real** (Faturamento - Custo de Combustível Estimado - Custo Fixo Diário), crucial para a saúde financeira do motorista.
* **Transição Fullstack (`api_core.py`):** Criamos uma camada intermediária que desacopla a lógica de negócio (o "cérebro" do app) da interface de usuário. Isso garante que o Frontend (seja Web ou Mobile) possa consumir o Backend de forma eficiente, sem conhecer os detalhes internos do banco de dados.
* **Persistência de Dados (`database_manager.py`):** Implementação do padrão **UPSERT** (Update or Insert) para gerenciar logs diários, permitindo que o motorista edite logs do dia sem criar duplicidades.

### 2. Visão de Arquitetura e Tecnologia

| Componente | Função | Tecnologia | Status de Entrega |
| :--- | :--- | :--- | :--- |
| **Backend Core** | Regras de Negócio e Cálculos | Python (`analytics.py`) | **100% Concluído** |
| **API/Middleware** | Comunicação Front-Backend | Python (`api_core.py`) | **100% Concluído** |
| **Frontend PoC** | Prova de Conceito e UX | Streamlit (Python Puro) | **100% Concluído** |
| **Persistência** | Armazenamento Seguro de Logs | SQLite (`daily_log.db`) | Concluído (para PoC Local) |

### 3. As Fases do Projeto (Nossa História)

1.  **V0.1 - Prova de Conceito (CLI - `app.py`):** Implementação inicial da lógica de login, cadastro e cálculos, totalmente via Terminal. Esta versão validou a funcionalidade crítica.
2.  **V0.2 - Transição Fullstack (Web - `web_app.py`):** Refatoração da arquitetura para um modelo Web, usando Streamlit para criar uma interface de usuário acessível via navegador (Web/Mobile), visando a fase de Teste de Campo.

---

## 🚧 Status Atual: Em Teste de Campo

O projeto está atualmente em fase de **Teste de Campo com usuários reais (motoristas)**. O objetivo desta fase é coletar *feedback* sobre a usabilidade da interface e a relevância das métricas para guiar futuras melhorias e o desenvolvimento da próxima versão (V1.0), que incluirá:

* **Migração de DB:** Transição do SQLite (local) para **PostgreSQL** (nuvem) para garantir escalabilidade e persistência em um ambiente de produção.
* **Aprimoramento do Frontend:** Desenvolvimento de uma interface mais rica e responsiva (utilizando frameworks dedicados, como React ou Vue).

### Como Rodar o Projeto (Para Revisores/Recrutadores)

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/raphaallen/drivers-daily-log
    cd drivers_daily_log
    ```
2.  **Instale as Dependências:** (Recomendado Python 3.11/3.12)
    ```bash
    pip install -r requirements.txt
    ```
3.  **Inicie o Aplicativo Web:**
    ```bash
    streamlit run web_app.py
    ```
4.  Acesse `http://localhost:8501` no seu navegador.

---

**Obrigado por analisar nosso trabalho.** Este projeto demonstra não apenas a capacidade técnica em Python Fullstack, mas também a compreensão da arquitetura de software, visão de produto e foco no valor real para o usuário final.

*Desenvolvido com paixão por Rafael e com o suporte de uma Ferramenta de IA/LLM.*
