from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import getenv

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = os.environ["SMTP_PORT"]
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]

SMTP_FROM_NAME = os.environ["SMTP_FROM_NAME"]
SMTP_FROM_EMAIL = os.environ["SMTP_FROM_EMAIL"]

FRONTEND_RESET_URL = os.environ["FRONTEND_RESET_URL"]


def send_email_html(to_email: str, subject: str, html_content: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = to_email

    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())


def reset_password_template(reset_url: str, user_name: str | None = None):
    name = user_name or "Olá"

    return f"""
    <div style="font-family: Arial, sans-serif; background-color:#f6f6f6; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 0 10px #0002;">

            <h2 style="color:#333; text-align:center;">Redefinição de Senha</h2>

            <p style="font-size:15px; color:#444;">
                {name}, recebemos uma solicitação para redefinir sua senha.
            </p>

            <p style="font-size:15px; color:#444;">
                Clique no botão abaixo para continuar:
            </p>

            <div style="text-align:center; margin: 30px 0;">
                <a href="{reset_url}"
                   style="padding: 12px 25px; 
                          background-color:#007bff; 
                          color:white; 
                          text-decoration:none; 
                          border-radius:5px;
                          font-size:16px;">
                    Redefinir Senha
                </a>
            </div>

            <p style="font-size:14px; color:#666;">
                Este link é válido por <strong>15 minutos</strong>.
            </p>

            <hr style="margin-top:30px; border: none; border-top: 1px solid #eee;">

            <p style="font-size:12px; color:#999; text-align:center;">
                Caso você não tenha solicitado essa ação, apenas ignore este e-mail.
            </p>
        </div>
    </div>
    """
