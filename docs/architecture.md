# Organização e manutenção do código

O terminal e a interface web usam o mesmo `CitizenAgent`. A aplicação continua exigindo apenas Python 3.10 ou superior; não há etapa de build, framework web ou API paga.

## Python

| Arquivo | Responsabilidade |
| --- | --- |
| `src/sistema.py`, `src/cli.py` | Entrada e navegação pelo terminal |
| `src/knowledge_base.py` | Leitura, validação, índices e atualização atômica dos dados |
| `src/search.py` | Normalização, índice de termos, pontuação e ambiguidade |
| `src/agent.py` | Comandos, contexto da sessão e telemetria minimizada |
| `src/response.py`, `prompts/` | Apresentação das respostas com fontes e limites |
| `src/web_service.py` | Sessões web, consultas e dados dos indicadores |
| `src/web.py` | Rotas HTTP, validação de pedidos e inicialização do servidor |
| `src/evaluation.py` | Avaliação A/B e exportação dos resultados |

Os termos dos registros são normalizados ao carregar a base. Cada consulta normaliza somente a entrada e compara os conjuntos já preparados. A pontuação e os limites de ambiguidade permanecem os mesmos; adicionar dados continua sendo uma operação no JSON, seguida de reinicialização e testes.

O serviço web limita as sessões a 50. O servidor aceita corpos de até 8 KiB e valida os tipos de sessão, modelo, tema e reinício. Somente HTML de entrada, JavaScript, CSS e fonte dentro de `web/` são publicados; dados e módulos Python não são rotas estáticas. A lista de recursos é montada na inicialização: reinicie o servidor ao adicionar arquivos à interface.

## Interface

`web/index.html` contém as telas, os formulários, os ícones e os diálogos. `web/app.js` inicializa a aplicação, coordena a navegação e apresenta consultas e temas.

| Módulo | Responsabilidade |
| --- | --- |
| `web/js/api.js` | Requisições, limite de espera e mensagens de falha |
| `web/js/chat.js` | Conversas, histórico, envio e repetição de consultas |
| `web/js/voice.js` | Permissão, transcrição e interrupção do ditado |
| `web/js/notifications.js` | Diálogos, avisos e contador do sino |
| `web/js/preferences.js` | Preferência claro/escuro |
| `web/js/dom.js` | Seletores, escape de texto e animação das palavras |

Os módulos são nativos do navegador. A interface deve ser aberta pelo servidor local, não diretamente por `file://`. Textos de perguntas são inseridos como texto ou escapados antes da montagem de elementos. O histórico permanece privado ao módulo de chat, na memória da aba.

`web/style.css` importa quatro arquivos em ordem: `base.css` (elementos e componentes básicos), `components.css` (formulários, temas e diálogos), `conversation.css` (conversas e movimento) e `layout.css` (enquadramento, cores e adaptação à tela). A ordem é explícita para preservar a cascata. A refatoração removeu 120 declarações já substituídas por regras posteriores, mantendo os fluxos e a aparência verificados no navegador.

## Convenções

- Comentários curtos em português, usados para seções ou decisões relevantes.
- `.editorconfig` define UTF-8, espaços e fim de linha uniforme.
- `.prettierrc.json` define a formatação opcional de HTML, CSS e JavaScript.
- HTML estático fica no HTML; somente conteúdo dependente de dados é montado em JavaScript.
- Controles são ligados por identificadores, sem depender da posição dos botões no menu.
- Falhas de rede permitem repetir a mesma mensagem, sem duplicar a conversa.

Prettier e Black foram usados apenas na revisão do código. Não são necessários para executar o projeto. Testes de navegador usam Playwright e Edge apenas no ambiente de desenvolvimento.

## Validação

```bash
python -m unittest discover -s tests -v
python -m src.evaluation
python -m tests.run_usability
```

Com `python iniciar.py` em execução, os testes opcionais do navegador são:

```bash
python scripts/test_web_browser.py
python scripts/test_web_inputs.py
python scripts/test_web_chat.py
```

A organização facilita manutenção e crescimento da base, mas o servidor continua sendo um protótipo local. Não há implantação pública, autenticação, armazenamento permanente de conversas ou garantia de uso em produção.
