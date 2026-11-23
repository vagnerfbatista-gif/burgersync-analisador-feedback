"""
Módulo de Análise de Sentimento com Google Gemini (Layer 3 - Execução)
Integração com a API Gemini para categorização (Positivo, Neutro, Crítico) e extração de tags,
com tentativas (retries), backoff exponencial e contingência determinística local (Self-Annealing).
"""

import os
import json
import time
import re
import requests
from dotenv import load_dotenv

# Garantir carregamento das variáveis de ambiente
load_dotenv()

def _deterministic_local_fallback(comentario, nota=None):
    """
    Fallback determinístico local (Self-Annealing) para garantir operação contínua
    caso a API esteja fora do ar, atinja cota ou ocorra timeout.
    """
    comentario_lower = comentario.lower()
    
    criticos_keywords = [
        "pessimo", "péssimo", "horrivel", "horrível", "ruim", "errado", "errada",
        "cru", "crua", "estragado", "estragada", "atraso", "atrasou", "demora", "demorou",
        "sujo", "suja", "frio", "fria", "gelado", "gelada", "cabelo", "barata",
        "falta de respeito", "nunca mais", "decepção", "decepcionado", "nojento",
        "passei mal", "dinheiro de volta", "cancelar", "revoltado"
    ]
    
    positivos_keywords = [
        "maravilhoso", "maravilhosa", "excelente", "otimo", "ótimo", "otima", "ótima",
        "perfeito", "perfeita", "delicia", "delícia", "delicioso", "deliciosa",
        "adorei", "amei", "parabens", "parabéns", "muito bom", "muito boa",
        "recomendo", "top", "impecavel", "impecável", "sensacional", "melhor"
    ]

    is_critico = any(k in comentario_lower for k in criticos_keywords) or (nota is not None and int(nota) <= 2)
    is_positivo = any(k in comentario_lower for k in positivos_keywords) or (nota is not None and int(nota) >= 4)

    if is_critico and not is_positivo:
        sentimento = "Crítico"
    elif is_positivo and not is_critico:
        sentimento = "Positivo"
    elif is_critico and is_positivo:
        # Misto/Neutro ou Crítico se a nota for baixa
        sentimento = "Crítico" if (nota and int(nota) <= 2) else "Neutro"
    else:
        sentimento = "Neutro"

    # Extração de tags por mapeamento temático
    tags = []
    tag_map = {
        "Sabor": ["sabor", "gostoso", "delicia", "delícia", "tempero", "molho", "blend", "salgado", "sem sal", "maionese"],
        "Ponto da Carne": ["ponto", "cru", "passado", "suculento", "seco", "queimado"],
        "Entrega": ["entrega", "motoboy", "chegou", "demora", "atraso", "demorou", "rapido", "rápido"],
        "Temperatura": ["frio", "fria", "gelado", "gelada", "quente", "morno", "murna"],
        "Atendimento": ["atendimento", "balcão", "balcao", "whatsapp", "educado", "grosso", "demorou para responder"],
        "Embalagem": ["embalagem", "pacote", "amassado", "derramou", "aberto", "caprichado"],
        "Preço": ["caro", "barato", "preço", "preco", "custo", "promoção", "promocao"],
        "Pedido Errado": ["errado", "errada", "trocado", "faltou", "faltando", "esqueceu"]
    }

    for tag, terms in tag_map.items():
        if any(term in comentario_lower for term in terms):
            tags.append(tag)

    if not tags:
        tags = ["Experiência Geral"]

    # Gerar resumo sucinto
    resumo = f"Avaliação classificada como {sentimento.lower()} com foco em {', '.join(tags[:3])}."

    return {
        "sentimento": sentimento,
        "tags": tags,
        "resumo_ia": resumo,
        "_origem": "fallback_deterministico"
    }

def analyze_feedback(comentario, nota=None, cliente_nome=None):
    """
    Analisa o feedback usando a API Gemini com retry exponencial.
    Retorna dicionário estruturado:
    {
        "sentimento": "Positivo" | "Neutro" | "Crítico",
        "tags": [...],
        "resumo_ia": "..."
    }
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[AVISO] GEMINI_API_KEY não configurada no ambiente. Acionando fallback determinístico.")
        return _deterministic_local_fallback(comentario, nota)

    system_instruction = (
        "Você é um especialista sênior em CX e análise de feedbacks para restaurantes e hamburguerias artesanais. "
        "Analise a avaliação fornecida e responda ESTRITAMENTE em formato JSON com o seguinte esquema:\n"
        "{\n"
        '  "sentimento": "Positivo" | "Neutro" | "Crítico",\n'
        '  "tags": ["Tag1", "Tag2"],\n'
        '  "resumo_ia": "Resumo objetivo e conciso em 1 ou 2 frases da experiência do cliente."\n'
        "}\n"
        "Critérios de sentimento:\n"
        "- Crítico: Qualquer reclamação grave, atraso severo, comida fria/crua/estragada, pedido errado, grosseria ou nota 1-2.\n"
        "- Neutro: Comentários mornos, sugestões neutras, nota 3 ou equilíbrio entre prós e contras sem gravidade.\n"
        "- Positivo: Elogios à comida, velocidade, atendimento, simpatia, satisfação geral ou nota 4-5.\n"
        "Tags sugeridas: Sabor, Ponto da Carne, Entrega, Atendimento, Temperatura, Embalagem, Preço, Pedido Errado, Limpeza, Tempo de Espera."
    )

    user_prompt = f"Avaliação do Cliente:\n"
    if cliente_nome:
        user_prompt += f"Nome do Cliente: {cliente_nome}\n"
    if nota:
        user_prompt += f"Nota dada (1 a 5 estrelas): {nota}\n"
    user_prompt += f"Comentário: \"{comentario}\"\n"
    user_prompt += "Retorne apenas o JSON puro, sem markdown extra."

    # Modelos ativos e responsivos: gemini-3.1-flash-lite (ultra-rápido, sem 503), seguido por gemini-3.6-flash e gemini-3.8-flash
    candidate_models = ["gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-flash-latest"]
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instruction}\n\n{user_prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    max_retries = 2
    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content_parts = candidates[0].get("content", {}).get("parts", [])
                        if content_parts:
                            raw_text = content_parts[0].get("text", "").strip()
                            # Remover blocos ```json se houver
                            clean_text = re.sub(r"^```json\s*", "", raw_text)
                            clean_text = re.sub(r"\s*```$", "", clean_text).strip()
                            result = json.loads(clean_text)
                            
                            # Normalização
                            sentimento = result.get("sentimento", "Neutro")
                            if sentimento not in ["Positivo", "Neutro", "Crítico"]:
                                if "positiv" in sentimento.lower():
                                    sentimento = "Positivo"
                                elif "crític" in sentimento.lower() or "critic" in sentimento.lower():
                                    sentimento = "Crítico"
                                else:
                                    sentimento = "Neutro"
                            
                            tags = result.get("tags", [])
                            if isinstance(tags, str):
                                tags = [tags]
                                
                            resumo = result.get("resumo_ia") or "Análise realizada com sucesso."
                            
                            print(f"[SUCESSO] Feedback analisado com sucesso via Gemini ({model}): {sentimento}")
                            return {
                                "sentimento": sentimento,
                                "tags": tags,
                                "resumo_ia": resumo,
                                "_origem": f"gemini_{model}"
                            }
                elif response.status_code == 429:
                    print(f"[AVISO] Rate limit (429) no modelo {model}. Tentativa {attempt + 1}/{max_retries}...")
                    time.sleep(1.5 * (attempt + 1))
                else:
                    print(f"[AVISO] Resposta status {response.status_code} no modelo {model}: {response.text[:120]}")
                    break  # Tentar próximo modelo se erro 404/400
            except Exception as ex:
                print(f"[AVISO] Exceção ao chamar {model} (tentativa {attempt + 1}): {ex}")
                time.sleep(1.0)

    # Se todos os modelos/tentativas falharem:
    print("[INFO] Acionando fallback determinístico local com base em regras léxicas.")
    return _deterministic_local_fallback(comentario, nota)
