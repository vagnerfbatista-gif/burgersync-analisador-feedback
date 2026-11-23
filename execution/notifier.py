"""
Módulo de Alerta Determinístico (Layer 3 - Execução)
Responsável pelo envio de e-mails em caso de feedback Crítico,
com fallback automático e resiliente para gravação estruturada em .tmp/alerts.log.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_DIR = os.path.join(BASE_DIR, ".tmp")
ALERTS_LOG_FILE = os.path.join(TMP_DIR, "alerts.log")

def _ensure_tmp_dir():
    os.makedirs(TMP_DIR, exist_ok=True)

def record_local_alert(feedback_data, reason="SMTP não configurado"):
    """Grava o alerta de crise estruturado em .tmp/alerts.log."""
    _ensure_tmp_dir()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    nome = feedback_data.get("nome") or "Não informado"
    contato = feedback_data.get("contato") or "Não informado"
    pedido_id = feedback_data.get("pedido_id") or "Não informado"
    comentario = feedback_data.get("comentario") or "Sem comentário"
    tags_str = ", ".join(feedback_data.get("tags", [])) or "Sem tags"
    resumo = feedback_data.get("resumo_ia") or "Nenhum resumo disponível"
    fb_id = feedback_data.get("id") or "N/A"

    log_entry = (
        f"[{now_str}] [ALERTA CRÍTICO DISPARADO]\n"
        f"ID: {fb_id}\n"
        f"Pedido: {pedido_id}\n"
        f"Cliente: {nome}\n"
        f"Contato: {contato}\n"
        f"Sentimento: Crítico\n"
        f"Tags: {tags_str}\n"
        f"Resumo IA: {resumo}\n"
        f"Comentário Original: {comentario}\n"
        f"Destino: Fallback Local (.tmp/alerts.log) - Motivo: {reason}\n"
        f"{'-'*80}\n"
    )

    try:
        with open(ALERTS_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"[INFO] Alerta crítico gravado com sucesso em .tmp/alerts.log para o pedido {pedido_id}")
        return True
    except Exception as e:
        print(f"[AVISO] Erro ao gravar em .tmp/alerts.log: {e}")
        return False

def send_critical_alert(feedback_data):
    """
    Envia alerta imediato para a gerência sobre feedback Crítico.
    Tenta SMTP caso configurado no ambiente (.env).
    Se indisponível ou falhar, ativa fallback para .tmp/alerts.log.
    """
    if feedback_data.get("sentimento") != "Crítico":
        return False

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("ALERT_RECIPIENT_EMAIL") or os.getenv("GERENTE_EMAIL", "gerencia.burgersync@gmail.com")

    # Se faltar qualquer credencial SMTP, aciona fallback
    if not (smtp_host and smtp_user and smtp_pass):
        record_local_alert(feedback_data, reason="Credenciais SMTP ausentes no .env")
        return True

    # Preparação da mensagem
    pedido_id = feedback_data.get("pedido_id") or "Não informado"
    nome = feedback_data.get("nome") or "Cliente"
    contato = feedback_data.get("contato") or "Não informado"
    comentario = feedback_data.get("comentario") or ""
    resumo = feedback_data.get("resumo_ia") or ""
    tags = ", ".join(feedback_data.get("tags", []))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 [ALERTA DE CRISE] Avaliação Crítica - Pedido {pedido_id} ({nome})"
    msg["From"] = os.getenv("SMTP_FROM", smtp_user)
    msg["To"] = recipient

    text_body = (
        f"ALERTA GERENCIAL - FEEDBACK CRÍTICO DETECTADO\n\n"
        f"Cliente: {nome}\n"
        f"Contato: {contato}\n"
        f"Número do Pedido: {pedido_id}\n"
        f"Resumo da IA: {resumo}\n"
        f"Tags Detectadas: {tags}\n\n"
        f"Comentário do Cliente:\n\"{comentario}\"\n\n"
        f"Acesse o Painel Administrativo para tratar este caso imediatamente."
    )
    msg.attach(MIMEText(text_body, "plain", "utf-8"))

    try:
        port_num = int(smtp_port)
        with smtplib.SMTP(smtp_host, port_num, timeout=10) as server:
            server.ehlo()
            if port_num == 587:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(msg["From"], [recipient], msg.as_string())
        print(f"[SUCESSO] E-mail de alerta crítico enviado com sucesso para {recipient}")
        return True
    except Exception as e:
        print(f"[AVISO] Falha ao enviar via SMTP ({e}). Ativando fallback resiliente...")
        record_local_alert(feedback_data, reason=f"Erro de conexão SMTP: {e}")
        return True

def read_recent_alerts():
    """Lê os alertas gravados em .tmp/alerts.log."""
    if not os.path.exists(ALERTS_LOG_FILE):
        return []
    try:
        with open(ALERTS_LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        entries = [e.strip() for e in content.split("-" * 80) if e.strip()]
        return entries[-15:]  # Últimos 15 alertas
    except Exception as e:
        print(f"[AVISO] Falha ao ler .tmp/alerts.log: {e}")
        return []
