"""
Script de Testes e Validação Completa do Fluxo (BurgerSync)
"""

import sys
import os

# Ajusta path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from execution.storage import load_feedbacks, add_feedback, toggle_feedback_status, get_metrics
from execution.gemini_analyzer import analyze_feedback
from execution.notifier import send_critical_alert, read_recent_alerts
from app import app

def test_storage():
    print("[TESTE 1] Testando Storage...")
    feedbacks = load_feedbacks()
    assert isinstance(feedbacks, list), "Feedbacks deve ser uma lista"
    print(f" -> Feedbacks existentes carregados: {len(feedbacks)}")
    
    metrics = get_metrics()
    assert "total" in metrics
    print(f" -> Métricas calculadas: Total={metrics['total']}, Pos={metrics['positivos']}, Neu={metrics['neutros']}, Cri={metrics['criticos']}")

def test_gemini_analyzer():
    print("\n[TESTE 2] Testando Gemini Analyzer...")
    
    # Teste Positivo
    res_pos = analyze_feedback("Hambúrguer espetacular, carne suculenta e atendimento nota 10!", nota=5, cliente_nome="Teste Positivo")
    print(f" -> Positivo: {res_pos.get('sentimento')}, Tags: {res_pos.get('tags')}, Origem: {res_pos.get('_origem')}")
    assert res_pos.get("sentimento") == "Positivo"
    
    # Teste Crítico
    res_cri = analyze_feedback("Comida horrível! Chegou com 2 horas de atraso, o lanche veio gelado e errado!", nota=1, cliente_nome="Teste Crítico")
    print(f" -> Crítico: {res_cri.get('sentimento')}, Tags: {res_cri.get('tags')}, Origem: {res_cri.get('_origem')}")
    assert res_cri.get("sentimento") == "Crítico"

def test_notifier():
    print("\n[TESTE 3] Testando Notifier e Fallback .tmp/alerts.log...")
    fake_critico = {
        "id": "fb-test-999",
        "pedido_id": "ORD-TEST-999",
        "nome": "Cliente Teste",
        "contato": "(14) 99999-0000",
        "comentario": "Lanche estragado e com gosto estranho. Quero meu reembolso!",
        "sentimento": "Crítico",
        "tags": ["Sabor", "Qualidade"],
        "resumo_ia": "Cliente relata lanche com gosto estranho solicitando reembolso."
    }
    sucesso = send_critical_alert(fake_critico)
    assert sucesso is True
    recentes = read_recent_alerts()
    print(f" -> Alertas recentes registrados: {len(recentes)}")
    assert len(recentes) > 0

def test_flask_endpoints():
    print("\n[TESTE 4] Testando Endpoints Flask...")
    client = app.test_client()
    
    # GET /
    r_index = client.get("/")
    assert r_index.status_code == 200, f"Esperado 200 em /, obteve {r_index.status_code}"
    print(" -> GET / : OK (200)")

    # GET /admin
    r_admin = client.get("/admin")
    assert r_admin.status_code == 200, f"Esperado 200 em /admin, obteve {r_admin.status_code}"
    print(" -> GET /admin : OK (200)")

    # GET /api/stats
    r_stats = client.get("/api/stats")
    assert r_stats.status_code == 200
    print(f" -> GET /api/stats : OK (200) - Total: {r_stats.json.get('total')}")

    # POST /api/feedback
    novo_fb = {
        "nome": "João Validador",
        "contato": "(14) 98111-2233",
        "pedido_id": "ORD-5500",
        "nota": 5,
        "comentario": "O burger bacon crocante é sem dúvidas o melhor de Ourinhos!"
    }
    r_post = client.post("/api/feedback", json=novo_fb)
    assert r_post.status_code == 201
    criado = r_post.json.get("feedback")
    print(f" -> POST /api/feedback : OK (201) - ID gerado: {criado.get('id')} - Sentimento: {criado.get('sentimento')}")

    # Toggle Status
    r_tratar = client.post(f"/api/feedbacks/{criado.get('id')}/tratar")
    assert r_tratar.status_code == 200
    assert r_tratar.json.get("feedback", {}).get("status") == "tratado"
    print(f" -> POST /api/feedbacks/{criado.get('id')}/tratar : OK (200) - Novo status: tratado")

if __name__ == "__main__":
    test_storage()
    test_gemini_analyzer()
    test_notifier()
    test_flask_endpoints()
    print("\n[TODOS OS TESTES FORAM CONCLUÍDOS COM SUCESSO!]")
