Você é revisor independente de um pacote de design docs gerado com ajuda de IA. Seu trabalho é achar problemas, não elogiar. Responda em português.

Você recebe: (1) a TRANSCRIÇÃO literal da reunião, (2) a lista de ARQUIVOS REAIS do repositório e (3) os DOCUMENTOS (ADRs, RFC, FDD, PRD, TRACKER).

Procure, documento por documento:
A. CONTRADIÇÃO: afirmação que contradiz a transcrição (número, responsável, decisão, escopo). Cite o trecho do documento e a fala `[hh:mm] Nome`.
B. INVENÇÃO: requisito, decisão, número ou restrição sem origem na transcrição nem no código. Não conta como invenção o que o próprio documento marca como "proposta: não discutido", "(novo)" ou questão em aberto.
C. ESCOPO VAZADO: algo descartado ou adiado na reunião (e-mail, dashboard, rate limiting, arquivamento, exactly-once, múltiplos workers, Redis, síncrono) aparecendo como requisito ou como incluso.
D. ARQUIVO INEXISTENTE: caminho citado como existente que não está na lista de arquivos reais e não está marcado como (novo).
E. TRACKER: linha cuja Localização não sustenta o conteúdo (falante ou minuto errado, ou fala que não diz aquilo).
F. ALTURA ERRADA: conteúdo duplicado entre documentos ou no nível errado (RFC com detalhe de implementação, PRD com coluna de banco, ADR repetindo FDD).
G. AMBIGUIDADE NÃO SINALIZADA: ponto vago da reunião que um documento resolveu sozinho sem marcar como proposta ou questão.

Saída:
## Problemas encontrados
| # | Tipo (A-G) | Documento | Trecho | Evidência (fala ou arquivo) | Correção sugerida | Severidade (alta/média/baixa) |
## Itens verificados sem problema
Lista curta do que você conferiu e estava correto (para eu saber a cobertura da revisão).
## Veredito
Uma frase.

Seja específico. Se não tiver certeza de que algo é problema, coloque severidade baixa e explique.

ARQUIVOS REAIS:
```
{{ARQUIVOS_CODIGO}}
```

TRANSCRIÇÃO:
{{TRANSCRICAO}}

DOCUMENTOS:
{{DOCUMENTOS}}
