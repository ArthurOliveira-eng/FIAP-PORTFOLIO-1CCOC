# Auditoria do enunciado

Esta auditoria compara o enunciado fornecido com o código, os dados e os relatórios do repositório. A entrega acadêmica ainda tem itens administrativos pendentes por decisão do responsável.

## Requisitos funcionais

| Exigência | Situação | Evidência |
| --- | --- | --- |
| Pelo menos 15 registros e 3 temas | Atendido | `data/knowledge_base.json`: 30 registros em oito temas |
| ID, tema, pergunta/palavras-chave, resumo, fonte e data | Atendido | Campos obrigatórios validados em `src/knowledge_base.py` |
| Fontes identificáveis e limites das orientações | Documentado | URLs oficiais e revisão registrada em `docs/source_review.md` |
| Carregamento por Python de JSON | Atendido | `KnowledgeBase.load` |
| Arquivo ausente, vazio ou inconsistente | Atendido | Validações e testes em `tests/test_system.py` |
| Adicionar/corrigir dados sem reescrever a busca | Atendido | JSON e função administrativa `save_record` |
| Listas e dicionários por ID e tema | Atendido | `records`, `by_id`, `by_theme` e `search_index` |
| Perguntas livres e escolha de assunto | Atendido | CLI, menu web e chat |
| Hierarquia ou grafo com relações explicadas | Atendido | Tema → registro e grafo dirigido; `docs/search_strategy.md` |
| Continuidade por pelo menos três assuntos | Atendido | D02 → S05 → S03 → C01, com teste de navegação |
| Estratégia de busca e várias correspondências | Atendido | Cobertura de termos, bônus e margem de ambiguidade documentados |
| Condicionais para entrada, correspondência e ausência | Atendido | `src/agent.py`, `src/search.py` e `src/response.py` |
| Dois modelos de instrução/resposta | Atendido | `prompts/template_a.txt` e `prompts/template_b.txt` |
| Comparação e justificativa da escolha | Atendido | `tests/template_comparison.json` e README |
| Resposta com fonte e aviso de confirmação | Atendido | Templates e contratos de teste |
| Entrada vazia, opção inexistente, ambiguidade e fora de escopo | Atendido | Agente, mensagens de interface e casos de regressão |
| Alternativas quando não há orientação suficiente | Atendido | Temas, perguntas sugeridas e registros relacionados |
| Pelo menos 12 perguntas de teste | Atendido | 46 casos executados nos dois modelos, totalizando 92 avaliações |
| Diretas, reformulações, fora de escopo e 3 limitações | Atendido | `tests/test_questions.json` |
| Esperado, obtido, acerto/erro e tempo | Atendido | `tests/results.json`, `.csv` e `.md` |
| Taxa de acerto e tempo médio | Atendido | Relatórios gerados e tabela do README |
| Usabilidade com usuário ou roteiro | Atendido por roteiro | Oito tarefas automatizadas; nenhum participante humano declarado |
| Interpretação, limites e duas melhorias | Atendido | README, `docs/usability.md` e comparação A/B |
| Execução `python src/sistema.py` | Atendido | CLI mantida e testada; web é opcional |
| Uso de IA e validação crítica | Documentado | `docs/uso_ia.md` |
| Privacidade e caráter não oficial | Atendido no escopo | Sem coleta solicitada de dados pessoais; avisos e logs minimizados |

Os relatórios existentes não equivalem a uma avaliação independente. A revisão desta refatoração não revalidou o conteúdo atual de cada página governamental; as datas da base não foram alteradas. A captura real de voz depende do navegador e do microfone; os testes automatizados simulam os eventos de transcrição.

## Checklist de entrega

| Item | Situação |
| --- | --- |
| Repositório público | Confirmado pela API do GitHub durante a auditoria |
| Nome da equipe, integrantes e RMs | Integrantes e RMs registrados no README |
| Vídeo no YouTube como não listado | Link registrado no README |
| TXT contendo apenas os dois links | Contém os links do repositório e da demonstração |
| Envio do TXT na FIAP ON | Realizado |
| Python e operações demonstradas | Cobertos pelos testes locais. |
| Perguntas, respostas, busca, métricas, falhas e limites | Documentados no README e nos relatórios |
| Revisão crítica pela equipe | Feito pela equipe |

## Modelo oficial e Tabela 2

O [modelo oficial da coordenação](https://github.com/equipe1ccon/FIAP-PORTFOLIO-1CCON/blob/master/README.md) organiza o portfólio por ano, fase e pasta da atividade (`CAP-X-NOME-DA-ATIVIDADE-APRESENTADA-NO-PORTAL`). Essa orientação foi consultada diretamente. A estrutura atual mantém este projeto executável na raiz, com `src/`, `data/`, `prompts/`, `tests/`, `docs/` e `web/`.

O enunciado recebido contém o título da Tabela 2, mas não suas linhas. Também não informa o capítulo e o nome exato da pasta da atividade no Portal. Portanto, a conformidade exata dessa parte permanece pendente. Não foram inventados nomes de pastas nem copiadas todas as pastas genéricas do portfólio para simular atendimento.

Quando essas informações estiverem disponíveis, conferir o destino acadêmico da atividade e os nomes obrigatórios de arquivos sem duplicar o código-fonte.
