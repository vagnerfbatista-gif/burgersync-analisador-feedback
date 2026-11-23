"""
Orquestrador Principal - Sistema de Feedback BurgerSync Ourinhos (Layer 2)
Coordena a interface web (Flask), chamadas à API Gemini e persistência/alertas.
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

from execution.storage import (
    load_feedbacks,
    add_feedback,
    toggle_feedback_status,
    get_metrics
)
from execution.gemini_analyzer import analyze_feedback
from execution.notifier import send_critical_alert, read_recent_alerts

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

@app.route("/")
def index():
    """Página pública de coleta de feedback para os clientes."""
    return render_template("index.html")

@app.route("/admin")
def admin():
    """Painel gerencial interativo para monitoramento e tratativa dos feedbacks."""
    return render_template("admin.html")

@app.route("/api/feedback", methods=["POST"])
def post_feedback():
    """Recebe e processa o feedback do cliente com IA Gemini e salva no banco JSON."""
    data = request.get_json() or {}
    
    nome = (data.get("nome") or "").strip()
    contato = (data.get("contato") or "").strip()
    comentario = (data.get("comentario") or "").strip()
    pedido_id = (data.get("pedido_id") or "").strip()
    try:
        nota = int(data.get("nota", 5))
    except (ValueError, TypeError):
        nota = 5

    # Validação mínima
    if not nome or not contato or not comentario:
        return jsonify({
            "success": False,
            "error": "Nome, contato e comentário são obrigatórios para registrar seu feedback."
        }), 400

    print(f"[INFO] Processando avaliação de '{nome}' (Pedido: {pedido_id or 'N/A'}, Nota: {nota})...")

    # 1. Análise com IA Gemini (com retry e fallback determinístico)
    analise = analyze_feedback(comentario=comentario, nota=nota, cliente_nome=nome)

    sentimento = analise.get("sentimento", "Neutro")
    tags = analise.get("tags", [])
    resumo_ia = analise.get("resumo_ia", "")

    # 2. Montagem do registro de feedback
    feedback_item = {
        "nome": nome,
        "contato": contato,
        "pedido_id": pedido_id,
        "nota": nota,
        "comentario": comentario,
        "sentimento": sentimento,
        "tags": tags,
        "resumo_ia": resumo_ia,
        "status": "pendente",
        "alerta_disparado": False
    }

    # 3. Disparo de Alerta de Crise se Crítico
    if sentimento == "Crítico":
        disparou = send_critical_alert(feedback_item)
        feedback_item["alerta_disparado"] = bool(disparou)

    # 4. Persistência no banco JSON determinístico
    salvo = add_feedback(feedback_item)
    print(f"[SUCESSO] Feedback gravado com sucesso. ID: {salvo.get('id')}")

    return jsonify({
        "success": True,
        "message": "Feedback recebido e analisado com sucesso!",
        "feedback": salvo
    }), 201

@app.route("/api/feedbacks", methods=["GET"])
def get_feedbacks():
    """Retorna a lista de feedbacks cadastrados."""
    feedbacks = load_feedbacks()
    return jsonify({
        "success": True,
        "feedbacks": feedbacks
    })

@app.route("/api/feedbacks/<feedback_id>/tratar", methods=["POST"])
def tratar_feedback(feedback_id):
    """Alterna o status do feedback entre 'pendente' e 'tratado'."""
    atualizado = toggle_feedback_status(feedback_id)
    if atualizado:
        return jsonify({
            "success": True,
            "feedback": atualizado
        })
    return jsonify({
        "success": False,
        "error": "Feedback não encontrado."
    }), 404

@app.route("/api/stats", methods=["GET"])
def stats():
    """Retorna estatísticas e métricas consolidadas dos feedbacks."""
    metricas = get_metrics()
    return jsonify(metricas)

@app.route("/api/alerts/log", methods=["GET"])
def alerts_log():
    """Retorna o histórico recente de alertas críticos registrados em .tmp/alerts.log."""
    alerts = read_recent_alerts()
    return jsonify({
        "success": True,
        "alerts": alerts
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[INFO] Iniciando BurgerSync Feedback Analyzer em http://localhost:{port}")
    app.run(host=host, port=port, debug=False)
