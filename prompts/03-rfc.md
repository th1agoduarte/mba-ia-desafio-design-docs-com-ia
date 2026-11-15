Papel: tech lead submetendo uma proposta técnica para revisão do time, em português.

Entradas: TRANSCRICAO.md, ADRs já escritos em docs/adrs/ e o inventário revisado.

Escreva docs/RFC.md, com no máximo ~4 páginas (≈1.800 palavras), com as seções: Metadados (autor, status, data, revisores = os 5 participantes da reunião), TL;DR, Contexto e problema, Proposta técnica (visão de componentes e fluxo, SEM colunas de tabela, payloads completos ou códigos de erro: isso é do FDD), Alternativas consideradas, Questões em aberto, Impacto e riscos, Decisões relacionadas (links relativos para os ADRs).

Regras:
- Alternativas: só as que foram realmente colocadas na mesa e descartadas. Para cada uma, o trade-off que motivou o descarte e a origem `[hh:mm] Nome`. IDs RFC-ALT-0X.
- Questões em aberto, em duas listas:
  (a) levantadas na reunião e não decididas ou adiadas (rate limiting, e-mail, escala além de 1 worker, endurecer permissões, customer_id no body ou no path, arquivamento);
  (b) lacunas que surgiram ao consolidar a reunião com o código. Ex.: "5 tentativas" vs 5 intervalos, ordering durante retry, assinatura durante a convivência de secrets, armazenamento da secret, descoberta dos ids da DLQ.
  Não resolva nenhuma delas por conta própria. IDs RFC-Q-0X.
- Riscos no nível de arquitetura (não repita os riscos de negócio do PRD nem os de implementação do FDD). IDs RFC-RISK-0X.
- Cada item da proposta recebe um ID RFC-PROP-0X.
- Linguagem de decisão ("propomos", "decidido em ADR-00X"), não de implementação.
