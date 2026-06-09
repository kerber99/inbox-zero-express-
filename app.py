import os
import json
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Importa a nossa nova função de e-mail!
from email_fetcher import obter_texto_email

# Carrega a chave de API e credenciais do arquivo .env
load_dotenv()

# Verifica se a chave foi configurada
api_key = os.getenv("GEMINI_API_KEY")
email_user = os.getenv("EMAIL_USER")

if not api_key or api_key == "sua_chave_secreta_aqui":
    st.sidebar.warning("⚠️ Lembre-se de configurar a sua GEMINI_API_KEY no arquivo .env!")

if not email_user:
    st.sidebar.warning("⚠️ Para automação, configure EMAIL_USER e EMAIL_PASS no .env!")

# Inicializa o cliente do Gemini
try:
    client = genai.Client()
except Exception as e:
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
    
    # Chamando o modelo Gemini 2.5 Flash
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

# --- Configuração da Página do Streamlit ---
st.set_page_config(page_title="Inbox Zero Express", page_icon="⚡", layout="wide")

st.title("⚡ Inbox Zero Express")
st.subheader("Transforme o caos dos seus e-mails em uma lista de tarefas limpa e priorizada.")

# --- Sidebar para Filtros ---
with st.sidebar:
    st.header("⚙️ Filtros")
    filtro_urgencia = st.selectbox(
        "Filtrar por Urgência:",
        ["Todas", "Crítico", "Importante", "Baixo"]
    )

st.markdown("### 📥 Entrada de Dados")

# Criamos uma variável no session_state para guardar o texto da área de input
if 'texto_caixa' not in st.session_state:
    st.session_state['texto_caixa'] = ""

# Botão de automação do E-mail
if st.button("🔄 Buscar E-mails"):
    with st.spinner("Conectando ao seu servidor de e-mail..."):
        try:
            novos_emails = obter_texto_email(limite=5) # Traz os últimos 5
            if novos_emails:
                st.session_state['texto_caixa'] = novos_emails
                st.success("E-mails importados com sucesso! Verifique a caixa de texto abaixo.")
            else:
                st.info("Sua caixa de entrada está limpa! Nenhum e-mail no momento.")
        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar e-mails: {e}")

# Área para o usuário (agora recebe o valor atualizado da automação)
texto_input = st.text_area(
    "Ou cole manualmente aqui (se preferir):", 
    value=st.session_state['texto_caixa'],
    height=250
)
# Atualiza o estado caso o usuário edite o texto manualmente
st.session_state['texto_caixa'] = texto_input

# Função para estilizar as cores da tabela
def estilizar_urgencia(val):
    cor = ''
    if val == 'Crítico':
        cor = 'background-color: #ffcccc; color: #cc0000'
    elif val == 'Importante':
        cor = 'background-color: #fff2cc; color: #b38600'
    elif val == 'Baixo':
        cor = 'background-color: #e6f2ff; color: #005c99'
    return cor

if st.button("Processar e Priorizar 🚀", type="primary"):
    if texto_input.strip() == "":
        st.warning("Por favor, garanta que há texto na caixa antes de processar.")
    else:
        with st.spinner("A IA está organizando sua vida... Aguarde..."):
            try:
                resultado_json = analisar_emails(texto_input)
                lista_alertas = resultado_json.get("alertas", [])
                
                if lista_alertas:
                    st.session_state['dados_alertas'] = lista_alertas
                else:
                    st.error("Não foi possível identificar e-mails no texto fornecido.")
                    
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar com a IA: {e}")

# --- Exibição dos Dados ---
if 'dados_alertas' in st.session_state:
    lista_alertas = st.session_state['dados_alertas']
    df = pd.DataFrame(lista_alertas)
    
    if filtro_urgencia != "Todas":
        df = df[df["urgencia"].str.lower() == filtro_urgencia.lower()]
    
    if df.empty:
        st.info("Nenhum item corresponde ao filtro selecionado.")
    else:
        df_display = df.copy()
        df_display.columns = ["Remetente", "Assunto", "Urgência", "Resumo da IA", "O que você deve fazer (Action Item)"]
        
        st.success("Pronto! Aqui está o seu plano de ação:")
        
        st.dataframe(
            df_display.style.map(estilizar_urgencia, subset=['Urgência']),
            use_container_width=True
        )
        
        criticos = sum(1 for x in lista_alertas if x['urgencia'].lower() == 'crítico')
        st.metric(label="Tarefas Críticas Pendentes", value=criticos)
        
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Tabela em CSV",
            data=csv,
            file_name='inbox_zero_prioridades.csv',
            mime='text/csv',
        )
