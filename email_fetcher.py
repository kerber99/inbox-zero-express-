import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

# Carrega variáveis do ambiente
load_dotenv()

def obter_texto_email(limite=5):
    usuario = os.getenv("EMAIL_USER")
    senha = os.getenv("EMAIL_PASS")
    # O padrão é imap.gmail.com, se você usar outlook, será imap-mail.outlook.com
    servidor_imap = os.getenv("IMAP_SERVER", "imap.gmail.com")

    if not usuario or not senha:
        raise ValueError("As credenciais EMAIL_USER ou EMAIL_PASS não estão configuradas no .env")

    try:
        # Conecta no servidor IMAP via porta segura SSL
        imap = imaplib.IMAP4_SSL(servidor_imap)
        imap.login(usuario, senha)
        imap.select("INBOX")

        # Procura e-mails NÃO LIDOS ("UNSEEN")
        status, mensagens = imap.search(None, "UNSEEN")
        if status != "OK":
            return ""

        ids_emails = mensagens[0].split()
        
        # Pega apenas os "N" mais recentes para a IA não se perder e não gastar muitos tokens
        ids_recentes = ids_emails[-limite:]
        
        if not ids_recentes:
            return ""

        texto_consolidado = ""
        
        for e_id in ids_recentes:
            status, dados = imap.fetch(e_id, "(RFC822)")
            for parte in dados:
                if isinstance(parte, tuple):
                    msg = email.message_from_bytes(parte[1])
                    
                    # Decodificando o Assunto com segurança
                    assunto = ""
                    if msg["Subject"]:
                        assunto_tuple = decode_header(msg["Subject"])[0]
                        if isinstance(assunto_tuple[0], bytes):
                            assunto = assunto_tuple[0].decode(assunto_tuple[1] or "utf-8", errors="ignore")
                        else:
                            assunto = assunto_tuple[0]
                            
                    # Pegando Remetente
                    remetente = msg.get("From", "Desconhecido")
                    
                    # Pegando Corpo do Texto (Apenas texto simples, ignorando HTML rebuscado)
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
                            
                    # Limita o corpo do e-mail para não estourar tokens se for uma newsletter muito longa
                    corpo_curto = corpo[:800].strip()
                    
                    texto_consolidado += f"De: {remetente}\nAssunto: {assunto}\nMensagem:\n{corpo_curto}\n\n====================\n\n"
                    
        imap.logout()
        return texto_consolidado.strip()
        
    except Exception as e:
        raise RuntimeError(f"Erro ao acessar o e-mail (IMAP): {e}")
