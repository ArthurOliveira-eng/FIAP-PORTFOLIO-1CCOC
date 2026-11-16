# Avaliação de usabilidade por roteiros

O enunciado permite usar roteiros em vez de participantes. Oito roteiros estão em `tests/usability_tasks.json` e executam a interface real em subprocessos com `python -m tests.run_usability`. Os resultados incluem saída real, código de encerramento, verificações de conclusão, quantidade de ações e tempo de processo. Não há participantes humanos.

| Tarefa | Resultado pretendido | Dificuldade prevista |
| --- | --- | --- |
| U01 | Consultar documentos e abrir a emissão da CIN | É preciso selecionar um ID após o tema |
| U02 | Recuperar senha esquecida do gov.br | A recuperação ocorre somente no serviço oficial |
| U03 | Esclarecer a consulta sobre CPF | Uma consulta ampla exige esclarecimento |
| U04 | Retomar após entrada vazia ou opção inválida | Há interações extras antes de uma orientação útil |
| U05 | Reconhecer serviço estrangeiro fora do escopo | A base não atende a esse pedido |
| U06 | Navegar por D02 → S05 → S03 | É preciso escolher os IDs relacionados |
| U07 | Sair de um tema antes de perguntar sobre outro | O filtro ativo pode ocultar resultados de outros temas |
| U08 | Preparar comprovantes para reclamação | Os comprovantes devem ficar fora do assistente |

Indicadores: roteiros concluídos / total, média de ações prescritas sem o comando `sair` e tempo médio de processo. São indicadores de automação. Eles não medem tempo humano, compreensão, esforço cognitivo, compatibilidade com tecnologias assistivas ou satisfação. As dificuldades são observações de projeto e custos previstos, não depoimentos de participantes.

Analise as transcrições de falhas antes de afirmar que uma tarefa foi concluída. A aprovação de todos os roteiros mostra que esses caminhos funcionam, mas pode deixar de revelar linguagem confusa ou dificuldades de navegação. Um estudo posterior deve recrutar ao menos uma pessoa com consentimento, usar informações sintéticas, registrar dificuldades sem dados pessoais desnecessários e apresentar resultados reais de conclusão e compreensão. Melhore a visibilidade do tema ativo e ofereça escolhas numeradas conforme as dificuldades observadas.
