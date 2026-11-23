# 🍔 BurgerSync - Analisador Inteligente de Feedback (Ourinhos)

Sistema web completo para coleta, análise de sentimento em tempo real via **Google Gemini** e gestão centralizada de feedbacks de clientes para hamburguerias artesanais.

![Status](https://img.shields.io/badge/Status-100%25%20Conclu%C3%ADdo-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Framework](https://img.shields.io/badge/Framework-Flask%203.1-black)
![IA](https://img.shields.io/badge/IA-Google%20Gemini-orange)

---

## 🎯 Objetivo e Recursos

- **Página Pública do Cliente (`/`):** Interface intuitiva e responsiva (mobile-first) com avaliação por estrelas, coleta de dados para contato e submissão de comentários.
- **Análise Inteligente com Google Gemini:**
  - Classificação instantânea de sentimento: **Positivo**, **Neutro** ou **Crítico**.
  - Extração temática de tags (*Sabor, Ponto da Carne, Entrega, Atendimento, Temperatura, Embalagem, Preço*).
  - Resumo executivo gerado pela IA.
- **Alerta Automático de Crise (SMTP & Fallback):**
  - Feedbacks com sentimento **Crítico** disparam e-mail imediato para a gerência.
  - Fallback resiliente automático: quando o SMTP não estiver configurado, grava o alerta estruturado em `.tmp/alerts.log`.
- **Painel Administrativo (`/admin`):**
  - Métricas e KPIs dinâmicos (Total, % Positivo, % Neutro, % Crítico, Críticos Pendentes).
  - Banner de alerta em tempo real para crises não tratadas.
  - Tags em alta com filtro rápido ao clicar.
  - Filtros por sentimento, status (Pendente / Tratado), busca por palavras-chave e ordenação por data ou nota.
  - Botão de ação rápida para marcar avaliações como tratadas.
  - Visualizador integrado do log de alertas SMTP.
- **Arquitetura Resiliente (Self-Annealing):**
  - Contingência determinística local: caso a API externa sofra timeout, erro 503 ou atinja cota, o motor local analisa e categoriza o feedback sem interrupção de serviço.

---

## 🏗️ Arquitetura em 3 Camadas

1. **Layer 1 (Diretiva):** `projeto.md` definindo as regras de negócio, taxonomia de sentimentos e critérios de alerta.
2. **Layer 2 (Orquestração):** `app.py` integrando rotas Flask, controle de estado, APIs REST e despacho de eventos.
3. **Layer 3 (Execução):** Scripts determinísticos e isolados:
   - `execution/gemini_analyzer.py`: Integração com a API Gemini + fallback léxico.
   - `execution/storage.py`: Gestão atômica de I/O no banco `data/feedbacks.json`.
   - `execution/notifier.py`: Serviço de e-mail SMTP com fallback para `.tmp/alerts.log`.

---

## 🚀 Como Executar Localmente

### 1. Clonar o Repositório
```bash
git clone https://github.com/vagnerfbatista-gif/burgersync-analisador-feedback.git
cd burgersync-analisador-feedback
```

### 2. Configurar o Ambiente Virtual e Dependências
```bash
# Com uv (recomendado)
uv venv
uv pip install -r requirements.txt

# Ou com Python convencional
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Configurar o Arquivo `.env`
Crie ou edite o arquivo `.env` na raiz do projeto:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
PORT=5000

# Opcional para envio real de e-mails de alerta crítico:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app
ALERT_RECIPIENT_EMAIL=gerente@burgersync.com.br
```

### 4. Iniciar a Aplicação
```bash
python app.py
```
- Acesse a **Página do Cliente** em: `http://localhost:5000/`
- Acesse o **Painel do Administrador** em: `http://localhost:5000/admin`

---

## ☁️ Deploy em Nuvem (Render / Railway / Heroku)

O repositório já inclui os arquivos `Procfile` e `render.yaml` prontos para deploy contínuo:

### Deploy no Render:
1. Conecte sua conta do GitHub ao [Render.com](https://render.com).
2. Clique em **New +** &rarr; **Web Service**.
3. Selecione o repositório `burgersync-analisador-feedback`.
4. Configure:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
5. Em **Environment Variables**, adicione sua variável:
   - `GEMINI_API_KEY`: *(sua chave do Google Gemini)*
6. Clique em **Deploy**!
