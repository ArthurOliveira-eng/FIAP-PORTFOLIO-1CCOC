# Busca e navegação

A lista de registros JSON é indexada em dois dicionários: `by_id[id]` aponta para um registro e `by_theme[theme]` aponta para uma lista. Um terceiro dicionário representa o grafo de IDs relacionados. A ordem dos temas segue sua primeira aparição na base: Documentos, Serviços digitais e Apoio comunitário. Novos temas aparecem automaticamente.

Algoritmo de busca livre:

1. Remover espaços nas extremidades. Entradas vazias, longas demais e erros de menu são tratados antes da busca.
2. Normalizar acentos Unicode, converter para minúsculas, separar palavras pela pontuação, remover palavras comuns em português e aplicar os sinônimos explícitos de `src/search.py`.
3. Para cada registro do tema selecionado, ou de toda a base, consultar o conjunto de termos da pergunta e das palavras-chave em `search_index`. Esse índice é construído uma vez no carregamento da base. Os resumos não participam da busca, evitando que palavras incidentais dominem a classificação.
4. Calcular cobertura = termos distintos da consulta encontrados / termos distintos da consulta. Somar 0,20 quando uma expressão completa de palavras-chave com ao menos dois termos informativos estiver contida na consulta. A comparação usa conjuntos, não a ordem das palavras. A pontuação máxima é 1,20 e não representa uma probabilidade.
5. Descartar candidatos abaixo de 0,46. Ordenar por pontuação decrescente e depois por ID, de forma estável.
6. Se mais de um candidato estiver a até 0,12 da melhor pontuação, apresentar até cinco opções de esclarecimento. Consultas de uma palavra também pedem esclarecimento. Empates não selecionam silenciosamente o primeiro registro.
7. Caso contrário, apresentar o registro mais bem classificado com fonte, avisos e limitações.

Exemplos: `CPF` oferece D03 e D04. `inscrição no CPF` favorece D03 pelo bônus de expressão. `conta gov.br` solicita esclarecimento entre criação e níveis. `Esqueci minha senha do gov.br` encontra a recuperação de senha. `Cadastro Único` e `Cadastro Unico` são normalizados da mesma forma. Perguntas sobre habilitação canadense não encontram orientação confiável.

O vocabulário de sinônimos inclui formas como esqueci/recuperar, verificar/consultar, atualização/atualizar e níveis/nível. Ele é explícito e limitado; não é tradução automática nem compreensão semântica. Alterações devem ser avaliadas com novas consultas.

Um ID exato ignora a classificação textual e pode acessar outro tema, permitindo navegação pelo grafo. A seleção de tema lista seus assuntos sem afirmar que uma fonte foi consultada. Perguntas livres ficam restritas ao tema ativo até o comando `voltar`. Use `ajuda` para retornar ao menu, `relacionados` após consultar um registro e `sair` para encerrar. Os comandos antigos em inglês permanecem como aliases de compatibilidade, mas não são necessários para usar a aplicação.

O caminho D02 → S05 → S03 conecta emissão da CIN, validação da conta com a CIN e níveis de segurança. S03 → C01 continua para um serviço de consumidor que exige determinado nível de conta. C03/C04/C05 conectam inscrição, atualização e atendimento local do CRAS. As ligações indicam assuntos úteis, sem criar fatos ou regras automáticas de elegibilidade.

A normalização é linear no tamanho da entrada. Os termos dos registros são preparados uma vez e reutilizados nas consultas. Uma consulta percorre os n registros e compara pequenos conjuntos: aproximadamente O(n × vocabulário médio do registro), além da ordenação dos candidatos, adequado aos 15 registros. A consulta por ID tem custo médio O(1). A busca por tema acessa um dicionário e sua lista. Nenhum serviço externo de indexação é necessário.

Limitações: sem representações vetoriais aprendidas, classificador treinado, inferência semântica, correção aproximada de digitação ou tradução automática. Uma correspondência lexical pode ser incompleta ou falhar com termos desconhecidos. Palavras genéricas podem gerar ambiguidade. Respostas alternativas conservadoras e resumos fixos reduzem invenções, mas não garantem identificar perfeitamente a intenção. Os casos elaborados durante o desenvolvimento não são uma avaliação independente.
