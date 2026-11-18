# Citizen Assist AI

Protótipo independente de orientação ao cidadão, com interfaces textual e web para serviços públicos brasileiros. A interface, as orientações, os comandos e a documentação estão em português brasileiro (pt-BR). Os nomes originais dos serviços brasileiros e as páginas de referência em português são preservados quando necessário. A busca utiliza a base local, sem APIs pagas ou modelos generativos. O ditado opcional depende do serviço do navegador e pode enviar áudio para transcrição online, mediante confirmação do usuário.

## 1. Equipe e situação da entrega

| Campo | Valor |
| --- | --- |
| Projeto / nome provisório da equipe | Citizen Assist AI — nome da equipe aguardando confirmação |
| Responsável pelo repositório | Arthur Apolonio de Oliveira |
| RM Resp | rm571385 - Arthur Apolonio De Oliveira
| Outros integrantes e RMs: rm573611 - Bryan Lima Garcia | rm569195 - Matheus Bejarano Da Costa Resende
| Repositório público | https://github.com/ArthurOliveira-eng/FIAP-PORTFOLIO-1CCOC |
| Demonstração no YouTube (não listado) | Aguardando envio pela equipe; nenhum link fictício foi inserido |

O protótipo, o executor de avaliações, os roteiros de tarefas e o gerador de vídeo estão implementados. A entrega permanece incompleta até o preenchimento dos integrantes/RMs e de uma URL válida do vídeo não listado no YouTube. A execução local foi verificada no Windows com Python 3.14; consulte a [validação local](docs/local_validation.md). Os resultados do GitHub Actions são identificados separadamente.

Veja a [auditoria do enunciado e da entrega](docs/requirements_audit.md) para distinguir requisitos atendidos e pendências. A [organização do código](docs/architecture.md) descreve os módulos e as convenções de manutenção.

## 2. Problema, público e temas

Cidadãos frequentemente precisam identificar o órgão responsável e o próximo passo seguro sem navegar por vários portais. Este assistente oferece orientações concisas com fontes, sem processar solicitações, prestar atendimento oficial, fornecer aconselhamento jurídico individual ou decidir sobre elegibilidade.

Público-alvo: pessoas que buscam orientações básicas sobre serviços públicos brasileiros, estudantes que demonstram recuperação responsável de informações e avaliadores que analisam fontes e algoritmos. A interface foi adaptada para pt-BR para facilitar o uso pelo público brasileiro, conforme a preferência solicitada para esta versão.

| Tema | Registros | Assuntos |
| --- | --- | --- |
| Documentos | D01–D05 | Visão geral e emissão da CIN, inscrição e situação do CPF, Carteira de Trabalho Digital |
| Serviços digitais | S01–S05 | Criação e recuperação de conta gov.br, níveis de segurança, assinatura eletrônica e validação da CIN |
| Apoio comunitário | C01–C05 | Reclamações de consumidores e comprovantes, inscrição e atualização no Cadastro Único, CRAS |

## 3. Organização da base e recuperação de informações

A base JSON contém 15 registros. Cada registro inclui `id`, `theme`, `question`, `keywords`, `summary_guidance`, `reference`, `verification_date`, `confirmation_warning` e `related_ids`. As fontes foram consultadas em 16/11/2026; veja a [revisão das fontes](docs/source_review.md). A data de verificação registra uma consulta pontual e não garante que a página permaneça inalterada.

Listas preservam a ordem de exibição dos registros. Dicionários indexam os registros por ID e tema. A hierarquia segue tema → registro do assunto; um dicionário de adjacência dirigido conecta registros relacionados entre temas. Por exemplo: D02 (emissão da CIN) → S05 (validação da conta com a CIN) → S03 (níveis de segurança) → C01 (acesso a reclamações de consumidores). Uma ligação indica uma continuação útil, sem representar necessariamente um pré-requisito oficial.

A busca normaliza maiúsculas, minúsculas, acentos e pontuação, remove palavras comuns das perguntas, aplica um pequeno dicionário explícito de sinônimos e compara conjuntos de termos. A pontuação corresponde à proporção dos termos da consulta encontrados no registro, acrescida de um bônus de 0,20 quando uma expressão completa de palavras-chave com vários termos é encontrada. É uma pontuação de classificação, não uma probabilidade. A pontuação mínima é 0,46. Candidatos com diferença de até 0,12 em relação à melhor pontuação geram um pedido de esclarecimento; a ordem dos IDs resolve empates na exibição. Uma consulta com apenas uma palavra informativa sempre solicita esclarecimento. IDs exatos e seleção por tema permitem navegação direta. Detalhes na [estratégia de busca](docs/search_strategy.md).

Os registros JSON podem ser adicionados ou corrigidos sem alterar as regras de busca. A validação verifica campos e tipos obrigatórios, textos e palavras-chave não vazios, IDs duplicados, URLs oficiais com HTTPS, datas de verificação no formato ISO e referências válidas no grafo. Bases inválidas são rejeitadas com uma mensagem compreensível. A função administrativa `save_record` valida toda a base antes da substituição atômica do arquivo. Consulte a [documentação de manutenção](docs/maintenance.md).

## 4. Regras de resposta e arquitetura do agente

| Componente do agente | Implementação |
| --- | --- |
| Percepção | `CitizenAgent.perceive` interpreta comandos, números de temas, IDs e texto |
| Raciocínio | `search` normaliza a entrada, aplica o filtro de tema, classifica candidatos e solicita esclarecimentos |
| Ação | `response` apresenta um registro validado usando um modelo de resposta versionado |
| Memória | `KnowledgeBase` carrega a base JSON verificada e seus índices |
| Salvaguardas | Sem geração livre de fatos; fonte, data de verificação, aviso de confirmação, limitação e aviso de caráter não oficial são obrigatórios |
| Observabilidade | Metadados de consultas em JSONL com proteção de privacidade, registros encontrados, nome do modelo de resposta, estado e latência |

O [modelo A](prompts/template_a.txt) apresenta a resposta e os campos obrigatórios em um parágrafo compacto. O [modelo B](prompts/template_b.txt) usa seções separadas e identificadas, sendo a opção padrão. Ambos usam os mesmos fatos fundamentados e limites. Seus cabeçalhos de instruções e formatos de apresentação são versionados como `template_a_v1` e `template_b_v1`; somente o texto após o delimitador de resposta é exibido. O processo preenche modelos de texto de forma determinística, sem executar instruções em um modelo de linguagem. A avaliação compara as mesmas perguntas nos dois formatos e verifica a presença de fonte e aviso, linhas separadas para fontes, tamanho das respostas e comprimento máximo das linhas. O modelo B foi escolhido por facilitar a leitura; essas medidas estruturais não comprovam a preferência de usuários reais.

Entradas vazias ou compostas apenas por pontuação geram um pedido de pergunta útil. Opções inválidas de menu exibem os temas disponíveis. Consultas ambíguas listam possíveis IDs. Quando não há correspondência, o sistema informa explicitamente que nenhuma fonte de orientação foi consultada e sugere perguntas ou temas. A entrada não altera as regras do sistema. O filtro contra tentativas de sobrescrever instruções é uma proteção adicional limitada; a segurança depende principalmente de retornar registros armazenados em vez de gerar fatos. Instruções desconhecidas, taxas, endereços locais, prazos e decisões individuais nunca são inventados.

Toda resposta com correspondência inclui a fonte e um aviso de confirmação. Registros com mais de 180 dias recebem um aviso adicional de desatualização. As fontes não são acessadas em tempo real durante a resposta. Um resultado parcialmente relacionado pode continuar incompleto: o usuário deve ler a limitação de escopo e confirmar os detalhes com o órgão responsável.

## 5. Plano de testes, indicadores medidos e interpretação

O conjunto de avaliação contém 31 casos: todos os 15 registros, perguntas reformuladas, normalização, perguntas fora do escopo, entradas vazias ou apenas com pontuação, consultas ambíguas, opções inválidas de menu, entradas longas demais e uma tentativa de sobrescrever instruções. Cada caso é executado nos dois modelos de resposta, totalizando 62 avaliações. Um resultado correto exige o estado esperado, os IDs exatos esperados, os trechos de resposta esperados e a aprovação das verificações de fonte e aviso. São testes funcionais de recuperação de informações, não uma avaliação independente de precisão semântica.

Taxa de acerto = respostas corretas / total. O tempo de consulta é medido com `perf_counter` durante uma chamada completa a `handle`, com a base já carregada e a telemetria desativada; a leitura e a apresentação do modelo de resposta estão incluídas. A latência varia conforme o hardware, o estado do cache e o sistema de arquivos. Resultados locais e de integração contínua não devem ser comparados como se os ambientes fossem idênticos.

<!-- METRICS:START -->
Execução em ambiente **local**, com Python 3.14.10, em 2026-11-17T02:39:33.598982+00:00.

| Modelo de resposta | Corretas / total | Taxa de acerto | Tempo médio de consulta (ms) |
| --- | ---: | ---: | ---: |
| template_a_v1 | 31 / 31 | 100,00% | 0,175335 |
| template_b_v1 | 31 / 31 | 100,00% | 0,147887 |

Cada modelo executa os mesmos casos independentes. A latência exclui o carregamento da base e a entrada/saída da telemetria, mas inclui a apresentação da resposta. Consulte `tests/results.json` e `tests/results.csv` para a tabela completa de resultados esperados e obtidos.
<!-- METRICS:END -->

A tabela registrada exporta resposta esperada, resposta obtida, classificação como correta ou erro, IDs encontrados e tempo individual em `tests/results.json` e `tests/results.csv`; `tests/results.md` contém uma tabela resumida para revisão. O arquivo `tests/template_comparison.json` registra a comparação A/B e exemplos de respostas. Os testes também cobrem arquivos de conhecimento ausentes, vazios ou malformados, estruturas inválidas, referências do grafo, atualizações, privacidade dos logs, falhas de gravação, fim da entrada (EOF), execução fora da pasta do projeto e fluxos completos da interface de linha de comando.

A usabilidade é avaliada com oito roteiros predefinidos executados na interface real de linha de comando, conforme permitido pelo enunciado. O arquivo `tests/usability_results.json` registra taxa de conclusão, quantidade de ações, tempo de processo e transcrições. Não houve participantes humanos; o tempo de processo não corresponde ao tempo de uma pessoa e nenhuma nota de satisfação foi inventada. As dificuldades previstas incluem esclarecer consultas amplas, selecionar IDs e sair dos filtros de tema. Veja a [metodologia de usabilidade](docs/usability.md).

Interpretação: a alta taxa de acerto demonstra que os exemplos escolhidos cumprem seus critérios esperados. Ela não comprova compreensão ampla da linguagem, cobertura completa das regras vigentes, decisões corretas de elegibilidade ou acessibilidade para usuários reais. Os modelos compartilham a mesma busca e os mesmos fatos; sua comparação verifica consistência de formatação, sem avaliar o raciocínio de um modelo de linguagem.

## 6. Como executar e testar localmente

### Interface web local

Requer apenas **Python 3.10 ou superior**. Não é necessário instalar pacotes para executar. Na pasta do projeto:

```bash
python iniciar.py
```

No Windows, também é possível **dar dois cliques em `iniciar.bat`** ou executar `py -3 iniciar.py`. Mantenha o terminal aberto enquanto usa a aplicação. Para encerrar, pressione **Ctrl+C** nesse terminal. Se a porta 8000 já estiver ocupada, use `python src/web.py --sem-log --porta 8080` e abra `http://127.0.0.1:8080`.

Abra **http://127.0.0.1:8000** no navegador. A tela inicial é **Conversas**, com campo de mensagem na parte inferior e botão **Fale por voz** no cabeçalho. A interface segue as referências visuais fornecidas e se ajusta à janela, com rolagem dentro dos painéis. Utiliza HTML, CSS, JavaScript e um servidor da biblioteca padrão do Python. A fonte Inter é distribuída localmente com sua licença; nenhum recurso externo é necessário para carregar a interface.

Em **Conversas**, escreva a mensagem e pressione **Enter** ou clique em enviar. **Shift + Enter** quebra a linha. As mensagens seguintes continuam na mesma conversa; **+ Nova** inicia outra, com contexto separado. Selecione uma conversa à esquerda para retomar suas mensagens.

**Fale por voz** abre a tela de áudio mantendo o contexto da conversa. No centro, os controles são **Falar**, **Limpar** e **Editar**. **Falar** inicia o ditado em pt-BR após confirmação e permissão. Confira o texto no painel direito e envie pela lupa. **Editar** leva ao campo de pergunta; **Limpar** cancela o ditado e limpa a consulta. O aplicativo não armazena áudio, mas o serviço do navegador pode processá-lo online. Sem suporte ou permissão, a digitação continua disponível.

O botão de lua/sol alterna o modo escuro; apenas a preferência visual é salva no navegador. As notificações são eventos internos da aba: consultas concluídas, erros e fontes desatualizadas geram avisos visuais e contagem no sino. Abrir o sino marca os avisos como lidos; é possível limpar a lista. Não são notificações push de órgãos públicos nem do sistema operacional.

Faça uma pergunta em português, selecione um tema ou abra um assunto relacionado. A barra lateral oferece fontes, apoio comunitário, histórico temporário, indicadores reais e seleção dos modelos A/B. O sino apresenta avisos reais. A resposta completa do modelo selecionado está disponível abaixo da consulta. Fontes oficiais abrem em outra aba.

### Conversas, voz e animações

- **Consulta:** o campo de digitação e a pergunta ficam à direita; a resposta aparece no centro. A resposta mantém as fontes, os avisos e as limitações da base.
- **Voz:** durante o ditado, as palavras surgem progressivamente no centro e a pergunta aparece à direita. Confira ou edite o texto antes de clicar em Pesquisar.
- **Conversas:** tela independente para conversar por texto, com perguntas à direita e respostas à esquerda. O histórico agrupa as mensagens por conversa. Rever uma conversa não executa outra consulta; enviar uma nova mensagem continua seu contexto. **Apagar histórico** limpa todas as conversas da aba.
- **Movimento:** botões têm efeitos suaves de pressão e retorno; palavras e cartões entram gradualmente. Não há ondas de clique. A opção **Reduzir animações** e a preferência de acessibilidade do sistema desativam os efeitos.
- **Nova consulta:** limpa a consulta atual, mantendo as mensagens anteriores disponíveis no histórico da aba.

As capturas da interface serão adicionadas após o envio dos prints pelo responsável pelo projeto.

O histórico fica apenas na memória da aba e pode ser apagado. Recarregar a página inicia uma nova sessão. `--sem-log` desativa a telemetria no servidor. O servidor atende somente em `127.0.0.1`; ele é destinado ao uso local. Encerre o processo Python para desligá-lo. Para outra porta, use `python src/web.py --sem-log --porta 8080`.

As consultas web passam pelo mesmo `CitizenAgent.handle` do terminal. Tema, último registro e modelo de resposta são isolados por sessão. Não há respostas simuladas quando o servidor está indisponível. Consulte [a validação web](docs/web_validation.md).

### Interface de terminal

Requer Python 3.10 ou superior. A aplicação e os testes utilizam apenas a biblioteca padrão do Python. Na raiz do repositório, execute:

```bash
python src/sistema.py
```

No Windows, use `py -3` caso `python` não esteja disponível no PATH.

```bash
python -m unittest discover -s tests -v
python -m src.evaluation
python -m tests.run_usability
python scripts/create_demo.py --somente-texto
```

O primeiro comando verifica o comportamento do sistema. Os seguintes geram a avaliação registrada, a comparação A/B, o relatório de usabilidade e a transcrição da demonstração. A avaliação também atualiza o bloco de métricas deste README. Uma comparação que falha encerra a execução com código diferente de zero. Os resultados gerados refletem o ambiente em que foram executados.

```bash
python src/sistema.py --modelo template_a_v1 --sem-log
python src/sistema.py --base data/knowledge_base.json
```

Comandos: `1`, `2` e `3` selecionam temas; um ID, como `D02`, abre uma orientação; `relacionados` oferece assuntos relacionados; `voltar` remove o filtro de tema; `ajuda` mostra os temas; `sair` ou `0` encerra a sessão. Perguntas livres ficam restritas ao tema selecionado até o uso de `voltar`. IDs exatos permitem acessar registros de outros temas e continuar a navegação por assuntos relacionados. Esses comandos são digitados em português; os antigos aliases em inglês continuam aceitos por compatibilidade.

O GitHub Actions executa os mesmos testes no Python 3.12 e disponibiliza relatórios medidos, uma demonstração em MP4 e um pacote de evidências como artefatos. O fluxo de trabalho tem acesso somente de leitura ao repositório e não cria commits de arquivos gerados. Apenas a geração de vídeo requer ferramentas adicionais: FFmpeg e a fonte DejaVu Sans Mono no caminho Linux documentado. Essas ferramentas opcionais não são dependências da aplicação. Os artefatos expiram após 30 dias; baixe o vídeo e envie-o ao YouTube antes da entrega.

## 7. Exemplos, fontes e entradas inválidas

As entradas e respostas abaixo utilizam a interface em português brasileiro.

Entrada: `Como recuperar minha senha do gov.br?`

> Use a opção “Esqueci minha senha” no acesso oficial do gov.br. Siga os métodos de recuperação disponíveis para sua conta; procure o suporte oficial se esses métodos não estiverem disponíveis.

Fonte: [orientação oficial para recuperação de conta gov.br](https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/atendimento-gov.br/duvidas-na-conta-gov.br/recuperar-senha-da-conta-gov.br). A aplicação também mostra a data de verificação, o aviso de privacidade sobre senhas e códigos, as limitações e os assuntos relacionados.

Entrada: `Onde buscar atendimento do CRAS?`

> O CRAS oferece orientação gratuita de assistência social básica, incluindo informações sobre serviços sociais, direitos e Cadastro Único. Consulte seu município para identificar a unidade adequada e as condições de agendamento.

Fonte: [página oficial do serviço do CRAS](https://www.gov.br/pt-br/servicos/acessar-o-cras-centro-de-referencia-da-assistencia-social). Confirme horários de funcionamento e agendamentos com o município.

| Entrada | Comportamento |
| --- | --- |
| Texto vazio | Solicita uma pergunta ou tema |
| `99` | Explica que a opção de menu é inválida e lista os temas |
| `CPF` | Solicita esclarecimento entre inscrição e situação cadastral; permite escolher D03 ou D04 |
| Pergunta sobre habilitação para dirigir no Canadá | Informa que não há resposta confiável armazenada e oferece alternativas disponíveis |
| `1 → D02 → relacionados → S05 → relacionados → S03` | Demonstra a navegação por três assuntos relacionados entre temas |

## 8. Clareza, acessibilidade, privacidade e ética

A saída textual com rótulos funciona sem cores, gráficos, serviços pagos ou conexão de rede. A interface não solicita nomes, RMs, números de CPF, senhas, códigos, endereços ou renda. Os RMs são dados da entrega acadêmica, não entradas da aplicação. Quando um serviço oficial exigir legitimamente dados pessoais, forneça-os diretamente nesse serviço.

Por padrão, os logs contêm apenas o tamanho da entrada, termos de vocabulário controlado e metadados operacionais; as consultas originais nunca são persistidas. Os logs são locais, não são rastreados pelo Git e podem ser desativados com `--sem-log`. Mesmo logs minimizados podem revelar assuntos de interesse: exclua `logs/` quando não forem mais necessários e não os publique. Não há serviço de análise nem transmissão para modelos externos. As perguntas e saídas sintéticas de avaliação são intencionalmente públicas.

O protótipo não é vinculado ao governo. Ele não agenda atendimentos, autentica usuários, acessa arquivos pessoais, envia solicitações nem promete benefícios. As fontes são páginas oficiais originais em português; os resumos utilizados pelo programa são paráfrases em português brasileiro. Conflitos entre fontes, traduções e mudanças nas regras exigem revisão humana. Consulte a [declaração de uso de IA](docs/uso_ia.md).

## 9. Demonstração e arquivo de links

O artefato de evidências do GitHub Actions inclui `citizen-assist-demo.mp4` quando a geração do vídeo é concluída com sucesso. Trata-se de uma demonstração renderizada automaticamente a partir da saída real capturada da interface de linha de comando, sem constituir gravação humana de tela ou estudo com usuários. A demonstração local apenas em texto não exige dependências adicionais. Consulte o [guia de vídeo](docs/demo_script.md).

URL do vídeo não listado no YouTube: **aguardando envio pela equipe**. Atualize este trecho e acrescente a URL real como segunda linha de [SUBMISSION_LINKS.TXT](SUBMISSION_LINKS.TXT). O TXT deve conter somente os dois links, sem rótulos ou explicações. Atualmente ele contém apenas o link do repositório e ainda não está pronto para envio. A publicação exige a conta da equipe no YouTube; o repositório não afirma que ela já ocorreu.

## 10. Conclusões, limitações e melhorias

O agente demonstra um fluxo completo de percepção → validação → recuperação → apresentação → fonte e limitação, utilizando listas, dicionários, leitura de arquivos, operações lógicas, navegação em grafo e procedimentos reproduzíveis. Esses recursos exercitam fundamentos de programação e a ênfase do enunciado nas fases 4, 5 e 6; como os materiais específicos dessas fases não foram fornecidos, não se afirma uma correspondência detalhada com o conteúdo do curso.

Limitações: apenas 15 registros selecionados e revisados, vocabulário limitado de consultas em português, correspondência lexical sem aprendizado semântico, ausência de correção de digitação, atualização automática de regras ou integração em tempo real, conjunto pequeno de testes elaborado durante o desenvolvimento, usabilidade avaliada por roteiros em vez de pessoas e tempos dependentes do ambiente. Uma resposta relacionada pode ser incompleta para perguntas detalhadas.

Melhorias prioritárias:

1. Executar um conjunto independente de testes e uma sessão real de usabilidade e acessibilidade com cidadãos que falam português, medindo compreensão, conclusão e dificuldade.
2. Ampliar as consultas revisadas em português, as reformulações e o tratamento de erros de digitação; ajustar os limites em um conjunto de desenvolvimento e apresentar resultados em um conjunto de testes reservado.
3. Adicionar uma fila de revisão das fontes, com acompanhamento de atualização e aprovação por um responsável; não aceitar mudanças coletadas automaticamente sem validação.
4. Melhorar a navegação, tornando o tema ativo mais visível e oferecendo opções numeradas de esclarecimento.

## Evidências de atendimento aos requisitos

| Requisito | Evidência / ação pendente |
| --- | --- |
| Repositório público | URL do repositório informada acima |
| Mínimo de 15 registros e 3 temas | `data/knowledge_base.json` |
| Python modular e memória configurável | `src/` e `prompts/` |
| Hierarquia e continuação por três assuntos | Dados do grafo, `search_strategy.md` e teste de regressão da navegação |
| Dois modelos de instrução e comparação | `prompts/` e `template_comparison.json` gerado pela avaliação |
| Testes diretos, reformulados, fora do escopo e de limitações | `tests/test_questions.json` e testes de regressão |
| Taxa de acerto, tempo e tabela de resultados esperados/obtidos | Arquivos `results.json`, `results.csv`, `results.md` e bloco de métricas do README |
| Usabilidade com roteiro de tarefas | Oito tarefas e arquivo gerado `usability_results.json` |
| Uso de IA e verificação crítica | `docs/uso_ia.md` e `docs/source_review.md` |
| Testes locais | Verificados no Windows com Python 3.14; veja `docs/local_validation.md` |
| Vídeo e YouTube não listado | Gerador de MP4 disponível; envio ao YouTube e URL real ainda pendentes |
| Equipe/RMs e entrega do TXT | Preencher dados dos integrantes e URL do YouTube antes da entrega |

A organização mantém o projeto executável na raiz. O modelo oficial organiza o portfólio por ano, fase e atividade; o destino exato deste trabalho e as linhas da Tabela 2 ainda não foram fornecidos. Essa conferência está pendente e detalhada na auditoria.

Os nomes de arquivos, campos JSON, funções, estados internos e identificadores de modelos permanecem estáveis como referências técnicas. Os textos apresentados ao usuário estão em pt-BR.
