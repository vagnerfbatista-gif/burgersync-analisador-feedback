"""
Módulo de Armazenamento Determinístico (Layer 3 - Execução)
Gerencia a persistência no banco de dados JSON data/feedbacks.json.
"""

import json
import os
import uuid
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FEEDBACKS_FILE = os.path.join(DATA_DIR, "feedbacks.json")

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FEEDBACKS_FILE):
        with open(FEEDBACKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_feedbacks():
    """Carrega todos os feedbacks do arquivo JSON."""
    _ensure_data_dir()
    try:
        with open(FEEDBACKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao carregar feedbacks.json: {e}")
        return []

def save_feedbacks(feedbacks):
    """Salva a lista completa de feedbacks no arquivo JSON."""
    _ensure_data_dir()
    temp_file = f"{FEEDBACKS_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
    os.replace(temp_file, FEEDBACKS_FILE)

def add_feedback(feedback_data):
    """
    Adiciona um novo feedback persistindo no arquivo JSON.
    Gera ID único e data_hora ISO caso não fornecidos.
    """
    feedbacks = load_feedbacks()
    if "id" not in feedback_data or not feedback_data["id"]:
        feedback_data["id"] = f"fb-{uuid.uuid4().hex[:6]}"
    
    if "data_hora" not in feedback_data or not feedback_data["data_hora"]:
        feedback_data["data_hora"] = datetime.now().astimezone().isoformat()
        
    if "status" not in feedback_data:
        feedback_data["status"] = "pendente"

    feedbacks.insert(0, feedback_data)
    save_feedbacks(feedbacks)
    return feedback_data

def toggle_feedback_status(feedback_id, new_status=None):
    """Alterna ou define o status de um feedback ('pendente' ou 'tratado')."""
    feedbacks = load_feedbacks()
    updated = None
    for fb in feedbacks:
        if fb.get("id") == feedback_id:
            if new_status:
                fb["status"] = new_status
            else:
                fb["status"] = "tratado" if fb.get("status") == "pendente" else "pendente"
            updated = fb
            break
    if updated:
        save_feedbacks(feedbacks)
    return updated

def get_metrics():
    """Calcula estatísticas agregadas dos feedbacks."""
    feedbacks = load_feedbacks()
    total = len(feedbacks)
    if total == 0:
        return {
            "total": 0,
            "positivos": 0,
            "neutros": 0,
            "criticos": 0,
            "perc_positivo": 0,
            "perc_neutro": 0,
            "perc_critico": 0,
            "pendentes": 0,
            "criticos_pendentes": 0,
            "tags_populares": []
        }

    positivos = sum(1 for fb in feedbacks if fb.get("sentimento") == "Positivo")
    neutros = sum(1 for fb in feedbacks if fb.get("sentimento") == "Neutro")
    criticos = sum(1 for fb in feedbacks if fb.get("sentimento") == "Crítico")
    pendentes = sum(1 for fb in feedbacks if fb.get("status") == "pendente")
    criticos_pendentes = sum(1 for fb in feedbacks if fb.get("sentimento") == "Crítico" and fb.get("status") == "pendente")

    # Contagem de tags
    tag_counts = {}
    for fb in feedbacks:
        for tag in fb.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    sorted_tags = sorted([{"tag": k, "count": v} for k, v in tag_counts.items()], key=lambda x: x["count"], reverse=True)

    return {
        "total": total,
        "positivos": positivos,
        "neutros": neutros,
        "criticos": criticos,
        "perc_positivo": round((positivos / total) * 100, 1),
        "perc_neutro": round((neutros / total) * 100, 1),
        "perc_critico": round((criticos / total) * 100, 1),
        "pendentes": pendentes,
        "criticos_pendentes": criticos_pendentes,
        "tags_populares": sorted_tags[:8]
    }
