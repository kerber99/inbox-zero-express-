# ⚡ Inbox Zero Express - AI Email Assistant

**Inbox Zero Express** é um agente autônomo e uma interface web interativa que utiliza Inteligência Artificial (Google Gemini 2.5) para classificar, priorizar e organizar sua caixa de entrada de e-mails automaticamente.

## 🚀 Funcionalidades

- **🤖 Agente Autônomo (Background Worker)**: Fica escutando sua caixa de e-mails de forma contínua em segundo plano.
- **🧠 Classificação Inteligente**: Usa LLM (Large Language Models) para determinar a urgência de e-mails extraindo o "Action Item" (o que você precisa fazer).
- **📂 Automação IMAP Real**: Move e-mails fisicamente no provedor (como o Gmail) criando pastas, marcando como lidos os spams e destacando com "estrelas" os e-mails vitais.
- **📊 Dashboard Interativo**: Interface Web desenvolvida em Streamlit para visualização clara, com filtros rápidos e métricas de produtividade.

## 🛠️ Tecnologias e Arquitetura
- **Python 3** (Back-end e Scripting)
- **Streamlit** (Front-end Web Application)
- **Google GenAI SDK** (Gemini 2.5 Flash para Processamento de Linguagem Natural)
- **IMAPLib & Email Parsing** (Conexão e manipulação segura de caixas de e-mail)
- **Pandas** (Estruturação e Exportação de Dados em CSV)

## 📦 Como testar o projeto localmente

1. Clone este repositório:
```bash
git clone https://github.com/SEU_USUARIO/inbox-zero-express.git
cd inbox-zero-express
```

2. Instale as bibliotecas necessárias:
```bash
pip install streamlit google-genai python-dotenv pandas
```

3. Configure as variáveis de ambiente:
Crie um arquivo `.env` na raiz do projeto (como o projeto usa `.gitignore`, suas credenciais ficarão seguras). Adicione as seguintes chaves:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
EMAIL_USER=seu_email@gmail.com
EMAIL_PASS=sua_senha_de_aplicativo_gerada
IMAP_SERVER=imap.gmail.com
```

4. **Para rodar a Interface Visual (Dashboard):**
```bash
streamlit run app.py
```

5. **Para iniciar o Robô Autônomo de Organização (Background Worker):**
```bash
python robo_inbox.py
```

## 🔒 Segurança
A automação utiliza conexões IMAP SSL seguras. O arquivo `.env` que armazena as chaves de API e a "Senha de App" está bloqueado pelo `.gitignore`, garantindo que não haja vazamento de credenciais na nuvem. Nunca commite seu `.env`.

---
*Projeto desenvolvido para resolver o caos das caixas de entrada utilizando automação inteligente.*
