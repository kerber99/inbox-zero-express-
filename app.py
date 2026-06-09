import os
import json
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Importa a nossa função de e-mail
try:
    from email_fetcher import obter_texto_email
except ImportError:
    obter_texto_email = None

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
email_user = os.getenv("EMAIL_USER")

if not api_key or api_key == "sua_chave_secreta_aqui":
    st.sidebar.warning("⚠️ Lembre-se de configurar a sua GEMINI_API_KEY no arquivo .env!")

if not email_user:
    st.sidebar.warning("⚠️ Para automação, configure EMAIL_USER e EMAIL_PASS no .env!")

try:
    client = genai.Client()
except Exception:
    client = None

def analisar_emails(texto_emails):
    if not client:
        raise ValueError("A chave da API do Gemini não está configurada corretamente.")
        
    prompt_sistema = """
    Você é um assistente especialista em produtividade e gerenciamento de tempo (Inbox Zero).
    Sua tarefa é analisar um bloco de texto que contém um ou mais e-mails/alertas e extrair as informações estruturadas.
    
    Para cada e-mail/alerta encontrado, você deve determinar:
    1. Remetente: Quem enviou (ou o sistema/empresa).
    2. Assunto: O tema principal.
    3. Urgência: Escolha estritamente entre [Crítico, Importante, Baixo].
    4. Resumo: Uma frase curta (máximo 15 palavras) explicando o que importa.
    5. Action Item: Uma tarefa clara, direta e acionável que o usuário precisa fazer.
    
    Você deve responder estritamente em formato JSON, seguindo esta estrutura:
    {
        "alertas": [
            {
                "remetente": "Nome",
                "assunto": "Assunto",
                "urgencia": "Crítico",
                "resumo": "Frase de resumo.",
                "action_item": "O que fazer."
            }
        ]
    }
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=texto_emails,
        config=types.GenerateContentConfig(
            system_instruction=prompt_sistema,
            response_mime_type="application/json",
            temperature=0.2 
        ),
    )
    
    return json.loads(response.text)

# --- Configuração da Página ---
st.set_page_config(page_title="Inbox Zero Express", page_icon="⚡", layout="wide")

st.title("⚡ Inbox Zero Express")
st.subheader("Transforme o caos dos seus e-mails em uma lista de tarefas limpa e priorizada.")

with st.sidebar:
    st.header("⚙️ Filtros")
    filtro_urgencia = st.selectbox(
        "Filtrar por Urgência:",
        ["Todas", "Crítico", "Importante", "Baixo"]
    )

st.markdown("### 📥 Entrada de Dados")

if 'texto_caixa' not in st.session_state:
    st.session_state['texto_caixa'] = ""

col_b1, col_b2, col_b3 = st.columns([2, 2, 4])

with col_b1:
    if st.button("🔄 Buscar E-mails"):
        if obter_texto_email:
            with st.spinner("Conectando ao seu servidor..."):
                try:
                    novos_emails = obter_texto_email(limite=5)
                    if novos_emails:
                        st.session_state['texto_caixa'] = novos_emails
                        st.success("E-mails importados com sucesso!")
                    else:
                        st.info("Sua caixa de entrada está limpa! Nenhum e-mail no momento.")
                except Exception as e:
                    st.error(f"Erro: {e}")
        else:
            st.error("Módulo de e-mail ausente.")

with col_b2:
    if st.button("🧹 Limpar Tudo"):
        st.session_state['texto_caixa'] = ""
        if 'dados_alertas' in st.session_state:
            del st.session_state['dados_alertas']
        st.rerun()

texto_input = st.text_area(
    "Cole os e-mails manualmente ou use o botão 'Buscar E-mails':", 
    value=st.session_state['texto_caixa'],
    height=250
)
st.session_state['texto_caixa'] = texto_input

def estilizar_urgencia(val):
    if val == 'Crítico':
        return 'background-color: #ffcccc; color: #cc0000'
    elif val == 'Importante':
        return 'background-color: #fff2cc; color: #b38600'
    elif val == 'Baixo':
        return 'background-color: #e6f2ff; color: #005c99'
    return ''

if st.button("Processar e Priorizar 🚀", type="primary"):
    if texto_input.strip() == "":
        st.warning("Garanta que há texto na caixa antes de processar.")
    else:
        with st.spinner("A IA está organizando sua vida..."):
            try:
                resultado_json = analisar_emails(texto_input)
                lista_alertas = resultado_json.get("alertas", [])
                
                if lista_alertas:
                    st.session_state['dados_alertas'] = lista_alertas
                else:
                    st.error("Não identificamos e-mails no texto.")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

# --- Exibição de Dados e Gráficos ---
if 'dados_alertas' in st.session_state:
    st.markdown("---")
    lista_alertas = st.session_state['dados_alertas']
    df = pd.DataFrame(lista_alertas)
    
    if filtro_urgencia != "Todas":
        df = df[df["urgencia"].str.lower() == filtro_urgencia.lower()]
    
    if df.empty:
        st.info("Nenhum item corresponde ao filtro.")
    else:
        st.success("Pronto! Aqui está o seu plano de ação detalhado:")
        
        # --- PAINEL DE ESTATÍSTICAS ---
        col_metrica, col_grafico = st.columns([1, 2])
        
        with col_metrica:
            st.markdown("#### 📊 Resumo")
            criticos = sum(1 for x in lista_alertas if x['urgencia'].lower() == 'crítico')
            importantes = sum(1 for x in lista_alertas if x['urgencia'].lower() == 'importante')
            baixos = sum(1 for x in lista_alertas if x['urgencia'].lower() == 'baixo')
            
            st.metric(label="🔴 Tarefas Críticas", value=criticos)
            st.metric(label="🟡 Tarefas Importantes", value=importantes)
            st.metric(label="🔵 Baixa Urgência", value=baixos)
            
        with col_grafico:
            st.markdown("#### Distribuição de Urgência")
            # Cria contagem para o gráfico de barras
            contagem_urgencia = pd.DataFrame(lista_alertas)["urgencia"].value_counts()
            st.bar_chart(contagem_urgencia)

        st.markdown("#### 📋 Lista de Tarefas (Action Items)")
        df_display = df.copy()
        df_display.columns = ["Remetente", "Assunto", "Urgência", "Resumo da IA", "O que fazer (Action Item)"]
        
        st.dataframe(
            df_display.style.map(estilizar_urgencia, subset=['Urgência']),
            use_container_width=True
        )
        
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Tabela em CSV",
            data=csv,
            file_name='inbox_zero_prioridades.csv',
            mime='text/csv',
        )
