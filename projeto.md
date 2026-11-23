# 📘 SOP: Avaliador de Feedback Hamburgueria

**Status:** Em Desenvolvimento | **Versão:** 1.0

## 1. Objetivo Principal

Desenvolver um sistema web completo para coletar, analisar e gerenciar avaliações de clientes de uma hamburgueria fictícia em Ourinhos. O sistema utiliza a API do Gemini para categorizar o sentimento (Positivo, Neutro ou Crítico) e extrair tags (como "Entrega", "Sabor", "Atendimento") dos feedbacks em tempo real. O objetivo é estruturar esses dados, disparar alertas automáticos para gestores em caso de crises e fornecer um painel administrativo para gestão e tomada de decisão rápida.

## 2. Arquitetura de 3 Camadas

* **Layer 1 (Diretiva):** Este documento, definindo as regras de negócio, os critérios de classificação de sentimentos e a lógica de alerta gerencial.


* **Layer 2 (Orquestração):** O Agente interpretando estas instruções, coordenando o fluxo de dados entre o frontend, as chamadas à API do Gemini e os disparos do backend.


* **Layer 3 (Execução):** Scripts determinísticos em Python na pasta `execution/`, responsáveis estritamente pelo backend, operações de I/O no banco JSON e conexões com o serviço SMTP.



## 3. Entradas e Requisitos (Inputs)

* **Dados necessários:** Chaves de API do Gemini e credenciais do serviço SMTP/API de e-mail no arquivo `.env`, além das submissões de texto enviadas pelos clientes via formulário web.


* **Ferramentas:** Python (para o backend), bibliotecas de requisição HTTP/Integração com Gemini, serviço de e-mail e tecnologias de frontend (HTML/JS/CSS) para as interfaces pública e administrativa.



## 4. Fluxo Operacional (Passo a Passo)

1. **Inicialização:** Verificar se o ambiente `.env` está configurado corretamente com as chaves necessárias.


2. **Coleta:** Receber a submissão de feedback textual do cliente pela página web pública.


3. **Processamento da IA:** O orquestrador aciona o script Python para enviar a frase à API do Gemini, exigindo o retorno do sentimento (Positivo, Neutro, Crítico) e a extração de tags específicas da experiência.


4. **Gerenciamento de Dados Temporários:** Armazenar dados em transição e logs de requisição na pasta `.tmp/` durante a execução da análise.


5. **Armazenamento Estruturado:** Salvar o review original em conjunto com a análise estruturada em um arquivo de banco de dados JSON.


6. **Alerta Automático:** Caso a análise retorne o status "Crítico", acionar imediatamente o serviço SMTP/API para disparar um e-mail com os detalhes do problema para o gerente.


7. **Atualização do Dashboard:** Disponibilizar os novos dados categorizados para a página web administrativa.



## 5. Definição de Sucesso (Outputs/Deliverables)

* **Entregáveis:**
* Página web pública para clientes.


* Backend em Python rodando a integração com Gemini e SMTP.


* Banco de dados JSON estruturado contendo todos os feedbacks.


* Painel administrativo interativo com filtros, ordenação e checkboxes para marcar avaliações como "lidas/tratadas".




* **Localização:** Os arquivos intermediários rodam localmente em `.tmp/`, mas os entregáveis finais (frontend e dashboard) devem estar hospedados em nuvem para acesso real.



## 6. Tratamento de Erros e Resiliência (Self-Annealing)

* Se houver falha em um script (ex: falha de conexão com a API do Gemini ou erro no SMTP): Ler o log de erro, ajustar o código determinístico na pasta `execution/` e testar a requisição novamente.


* Registrar o aprendizado: Atualizar esta diretiva documentando casos extremos, como timeout da API ou formatação inesperada de JSON, para evitar falhas futuras.


* O sistema deve se tornar mais robusto a cada falha corrigida, implementando *retries* (tentativas automáticas) nas requisições da Camada 3 para garantir que nenhum alerta crítico seja perdido devido a instabilidade de rede.

---

## 7. Log de Aprendizados de Self-Annealing

1. **Modelo Ativo do Google Gemini:**
   - As versões legadas `gemini-1.5-flash` e `gemini-2.5-flash` foram substituídas pela versão mais recente e veloz `gemini-3.6-flash` (com fallback robusto para contingência determinística local em caso de instabilidade de cota/rede).
   - Implementado mecanismo com tentativas e backoff exponencial garantindo que nenhum feedback seja perdido.

2. **Codificação e Terminal Windows:**
   - Tratamento de saídas de log no terminal para evitar `UnicodeEncodeError` com codificação CP1252 em ambientes Windows, utilizando tags de status estruturadas (`[INFO]`, `[SUCESSO]`, `[AVISO]`).
   - Sanitização de scripts de automação em lote (`.bat`) para evitar conflito com operadores de shell do CMD (como o operador `&` e aspas aninhadas).

3. **Resiliência e Integridade no Disparo de Alertas (SMTP):**
   - O disparo de e-mails conta com fallback automático para gravação estruturada em `.tmp/alerts.log` quando credenciais SMTP não forem informadas ou em quedas de rede externa.
   - Consolidação rigorosa dos dados do cliente (`nome`, `contato`, `pedido_id`, `comentario`) antes do acionamento do serviço de alerta, garantindo que nenhum e-mail seja despachado com dados anônimos ou em branco quando fornecidos pelo cliente.