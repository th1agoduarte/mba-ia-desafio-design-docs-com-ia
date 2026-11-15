Você é analista de requisitos e está montando o inventário rastreável de uma reunião técnica. Esse inventário vai alimentar PRD, RFC, FDD e ADRs, e cada linha precisa ter origem verificável.

Leia a TRANSCRIÇÃO abaixo, no formato `[hh:mm] Nome: fala`, e extraia **todos** os itens nas categorias:

| Categoria | O que entra |
|---|---|
| DECISAO | Algo que o grupo fechou ("decidido", "anotado", "fica", concordância explícita de quem conduz) |
| REQ_FUNCIONAL | Comportamento que o sistema precisa ter (endpoints, filtros, histórico...) |
| REQ_NAO_FUNCIONAL | Latência, limites, timeouts, segurança de transporte, tamanho de payload... |
| RESTRICAO | Limitação imposta (stack, infra, prazo, processo) |
| ALTERNATIVA_DESCARTADA | Opção colocada na mesa e rejeitada. Registre o motivo do descarte |
| ADIADO_OU_FORA | Algo explicitamente deixado para depois ou fora de escopo |
| QUESTAO_ABERTA | Ponto levantado e não decidido ("observar", "decidir depois", "problema do futuro") |
| GANCHO_CODIGO | Menção a arquivo, classe, função, tabela ou padrão do código existente |
| DETALHE_TECNICO | Formato de payload, headers, nomes de tabela, ids, etc. |
| CONTEXTO_NEGOCIO | Clientes, motivação, prazo, métricas de sucesso |

Regras obrigatórias:
1. Uma linha por item. Para cada item, informe o timestamp e o falante **exatamente** como aparecem na transcrição (ex.: `[09:17] Diego`). Se o item foi proposto por uma pessoa e fechado por outra, informe as duas (`[09:15] Diego; [09:17] Larissa`).
2. Coluna "Trecho literal": copie de 5 a 20 palavras da fala, sem parafrasear.
3. Não infira nada que não foi dito. Se algo foi só mencionado de passagem, não vire DECISAO.
4. Separe com cuidado o que NÃO entra: tudo que foi descartado, adiado ou deixado em aberto vai em ALTERNATIVA_DESCARTADA, ADIADO_OU_FORA ou QUESTAO_ABERTA, nunca em REQ_*.
5. Para GANCHO_CODIGO, use apenas nomes que aparecem na fala. Abaixo está a lista dos arquivos reais do repositório. Na coluna "Arquivo real", aponte o arquivo correspondente **somente** se ele estiver na lista. Caso contrário, escreva `não existe (novo)`.
6. Ao final, liste em "Ambiguidades" os pontos em que a própria transcrição é vaga ou contraditória. Exemplos do tipo de coisa: números que não fecham, opções deixadas em "ou", termos usados com dois sentidos.

Formato de saída (Markdown, em português):

## Inventário
| # | Categoria | Item (uma linha) | Trecho literal | Origem | Arquivo real |
|---|---|---|---|---|---|

## Ambiguidades
- ...

## Contagem por categoria
| Categoria | Itens |
|---|---|

ARQUIVOS REAIS DO REPOSITÓRIO:
```
{{ARQUIVOS_CODIGO}}
```

TRANSCRIÇÃO:
{{TRANSCRICAO}}
