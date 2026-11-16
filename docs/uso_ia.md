# Uso de IA e validação crítica

## Ferramentas e usos

O OpenAI ChatGPT/Codex auxiliou no desenho dos módulos Python, implementação da busca lexical, modelos de instrução e resposta, elaboração dos casos de teste, planejamento de testes, documentação e revisão dos comportamentos esperados. Também apoiou a adaptação dos textos e da busca para português brasileiro. A ferramenta conectada do GitHub foi usada para consultar o repositório e preparar e publicar código. A navegação na internet foi usada na consulta às fontes oficiais brasileiras durante a implementação inicial. O protótipo final não chama modelos externos.

## Método de validação

Cada resumo foi comparado com descrições oficiais, sem ser aceito apenas por ter sido proposto por IA. Campos obrigatórios, formato das URLs oficiais, datas e ligações do grafo são validados em Python. Os resumos são intencionalmente curtos e não contêm decisões individuais. A procedência das informações e uma inconsistência entre fontes estão registradas em `source_review.md`.

A avaliação compara IDs e estados esperados, conteúdo obrigatório e saída real nos dois modelos versionados. Os testes de regressão verificam erros de entrada, base malformada, navegação entre temas, avisos das fontes, manutenção dos dados, privacidade dos logs e fluxos da interface em subprocessos. A versão em pt-BR inclui testes de acentos, comandos, ajuda e avisos. Apenas relatórios executados contam como evidência medida. O ambiente distingue execução local de GitHub Actions. Não são inventados tempos, participantes, satisfação, links do YouTube ou resultados de aprovação.

## O que a equipe deve compreender e revisar

Antes da entrega, cada integrante deve conseguir explicar normalização dos termos, cobertura da consulta e bônus por expressão, limites de ambiguidade, listas e dicionários, ligações do grafo, preenchimento de respostas com fontes, tratamento de erros e cálculo de métricas. O repositório explica essas decisões e inclui comandos reproduzíveis. O auxílio de IA não demonstra que a equipe já compreendeu ou validou tudo de forma independente; a revisão pelos integrantes e o preenchimento dos RMs continuam sendo responsabilidade da equipe.

Revise criticamente as respostas esperadas, execute testes locais, leia as respostas obtidas e as fontes e desafie o sistema com perguntas novas. O mesmo assistente ajudou a elaborar código e testes, portanto podem existir pontos cegos compartilhados. Alta taxa de acerto nos exemplos não comprova prontidão para produção nem precisão independente.

## Privacidade e limites

O protótipo não envia consultas a um modelo, não coleta documentos de solicitações e não alega vínculo oficial. As consultas originais não são gravadas em logs. São documentados os metadados de vocabulário controlado e as saídas sintéticas de teste. O vídeo opcional utiliza apenas entradas sintéticas.

Se uma versão futura incluir um modelo generativo, confira cada afirmação e URL com a base revisada, rejeite saídas sem fundamento e faça uma revisão explícita de privacidade. As garantias determinísticas atuais não comprovam o comportamento de uma futura integração com modelos de linguagem.
