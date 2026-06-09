import os
import time
import json
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from google import genai
from google.genai import types
from datetime import datetime

# Carrega configurações
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_PASS")
servidor_imap = os.getenv("IMAP_SERVER", "imap.gmail.com")

if not api_key or not email_user or not email_pass:
    print("ERRO CRÍTICO: Verifique se GEMINI_API_KEY, EMAIL_USER e EMAIL_PASS estão configurados no arquivo .env")
    exit()

# Inicializa IA
client = genai.Client()

def classificar_com_ia(remetente, assunto, corpo):
    prompt_sistema = """
    Você é um assistente de produtividade organizando uma caixa de e-mails.
    Sua única tarefa é analisar este e-mail e classificar sua urgência.
    A urgência DEVE SER EXATAMENTE UMA DESTAS TRÊS OPÇÕES: "Crítico", "Importante" ou "Baixo".
    
    Responda ESTRITAMENTE em formato JSON seguindo este modelo:
    {
        "urgencia": "Crítico",
        "resumo": "Uma frase resumindo o assunto do email"
    }
    """
    
    # Prepara o texto
    texto_para_ia = f"De: {remetente}\nAssunto: {assunto}\nCorpo da Mensagem:\n{corpo[:1000]}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=texto_para_ia,
            config=types.GenerateContentConfig(
                system_instruction=prompt_sistema,
                response_mime_type="application/json",
                temperature=0.1 
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Erro ao comunicar com a IA: {e}")
        # Default de segurança em caso de erro
        return {"urgencia": "Importante", "resumo": "Falha na classificação."}

def processar_inbox():
    try:
        # Conecta no IMAP
        imap = imaplib.IMAP4_SSL(servidor_imap)
        imap.login(email_user, email_pass)
        
        # Garante que as pastas da IA existam no seu e-mail
        pastas_ia = ["IA_Critico", "IA_Importante", "IA_Baixo"]
        for pasta in pastas_ia:
            try:
                imap.create(pasta)
            except:
                pass # Se a pasta já existir, ignora o erro
                
        # Olha a caixa principal
        imap.select("INBOX")
        
        # Procura os não lidos
        status, mensagens = imap.search(None, "UNSEEN")
        if status != "OK" or not mensagens[0]:
            imap.logout()
            return
            
        ids_emails = mensagens[0].split()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚨 {len(ids_emails)} novo(s) e-mail(s) encontrado(s)! Iniciando análise IA...")
        
        for e_id in ids_emails:
            status, dados = imap.fetch(e_id, "(RFC822)")
            for parte in dados:
                if isinstance(parte, tuple):
                    msg = email.message_from_bytes(parte[1])
                    
                    # Decodificações
                    assunto = ""
                    if msg["Subject"]:
                        assunto_tuple = decode_header(msg["Subject"])[0]
                        if isinstance(assunto_tuple[0], bytes):
                            assunto = assunto_tuple[0].decode(assunto_tuple[1] or "utf-8", errors="ignore")
                        else:
                            assunto = assunto_tuple[0]
                    
                    remetente = msg.get("From", "Desconhecido")
                    
                    corpo = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    corpo = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                                except:
                                    pass
                    else:
                        try:
                            corpo = msg.get_payload(decode=True).decode(errors="ignore")
                        except:
                            pass
                            
                    print(f"⏳ Processando: '{assunto[:40]}...'")
                    
                    # Chama o Gemini
                    resultado = classificar_com_ia(remetente, assunto, corpo)
                    urgencia = resultado.get("urgencia", "Importante")
                    
                    # Define o destino com base na Urgência
                    pasta_destino = "IA_Importante"
                    
                    if urgencia == "Crítico":
                        pasta_destino = "IA_Critico"
                        imap.store(e_id, '+FLAGS', '\\Flagged') # Adiciona Estrela
                    elif urgencia == "Baixo":
                        pasta_destino = "IA_Baixo"
                        imap.store(e_id, '+FLAGS', '\\Seen')    # Marca como lido
                        
                    # MÁGICA: Copia para a nova pasta e deleta da Inbox original
                    imap.copy(e_id, pasta_destino)
                    imap.store(e_id, '+FLAGS', '\\Deleted')
                    
                    print(f"✅ Classificado como [{urgencia}]. E-mail movido para a pasta '{pasta_destino}'.")
                    
        # Confirma as remoções (Move de verdade)
        imap.expunge()
        imap.logout()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Caixa de entrada organizada com sucesso! Aguardando novos e-mails...")
        
    except Exception as e:
        print(f"❌ Erro de conexão com o servidor de E-mail: {e}")

if __name__ == "__main__":
    print("="*50)
    print("🤖 ROBÔ INBOX ZERO EXPRESS INICIADO")
    print("="*50)
    print("Ele ficará rodando invisível no fundo organizando seus e-mails.")
    print("Pressione CTRL+C a qualquer momento para parar.")
    print("Aguardando novos e-mails...\n")
    
    while True:
        processar_inbox()
        # Descansa 60 segundos antes de olhar a caixa de novo
        time.sleep(60)
