import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from servidor.config import SMTP_USER, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT, EMAIL_DESTINO

log = logging.getLogger("server.mailer")

conf = ConnectionConfig(
    MAIL_USERNAME=SMTP_USER,
    MAIL_PASSWORD=SMTP_PASSWORD,
    MAIL_FROM="nao-responda@meumvp.com", 
    MAIL_PORT=SMTP_PORT,
    MAIL_SERVER=SMTP_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False
)

async def enviar_notificacao_email(filename: str, device_id: str):
    print(f"\n[DEBUG EMAIL] ---> Iniciando envio para o arquivo: {filename} <--- \n")
    
    if not SMTP_USER or not EMAIL_DESTINO:
        print("[DEBUG EMAIL] ---> ERRO: Credenciais SMTP estão vazias no .env! <---")
        log.warning("Credenciais SMTP não configuradas. Pulando envio de e-mail.")
        return

    lista_emails = [email.strip() for email in EMAIL_DESTINO.split(",") if email.strip()]

    html = f"""
    <h3>Atualização de Arquivo</h3>
    <p>O arquivo <strong>{filename}</strong> foi modificado ou adicionado.</p>
    <p>Dispositivo de origem: {device_id}</p>
    """

    message = MessageSchema(
        subject=f"Sync Alert: {filename} atualizado",
        recipients=lista_emails, 
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"\n[DEBUG EMAIL] ---> SUCESSO: E-mail enviado! <---\n")
        log.info(f"E-mail de notificação enviado com sucesso para {filename}")
    except Exception as e:
        print(f"\n[DEBUG EMAIL] ---> FALHA CRÍTICA AO ENVIAR: {e} <---\n")
        log.error(f"Falha ao enviar e-mail: {e}")