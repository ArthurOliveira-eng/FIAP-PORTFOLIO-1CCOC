# Validação local

Validação executada no Windows com Python 3.14 em 16/11/2026, após a refatoração. A interface, os comandos, as orientações e os roteiros utilizam português brasileiro. `tests/results.json` registra ambiente, data, hashes da base e dos casos; o commit é informado quando a execução recebe `GITHUB_SHA`.

| Verificação | Comando | Resultado |
| --- | --- | --- |
| Regressão | `py -3 -m unittest discover -s tests -v` | 30 testes aprovados, incluindo 7 contratos HTTP |
| Busca e respostas | `py -3 -m src.evaluation` | 31/31 casos aprovados por modelo, 62 avaliações no total |
| Usabilidade por roteiro | `py -3 -m tests.run_usability` | 8/8 tarefas concluídas |
| Transcrição da demonstração | `py -3 scripts/create_demo.py --somente-texto` | Dez cenas e a cena de métricas geradas |
| Interface web | `scripts/test_web_browser.py`, `test_web_inputs.py`, `test_web_chat.py` | Fluxos, voz simulada e enquadramento verificados no Edge |

Os tempos medidos na execução atual estão no README e nos relatórios gerados. Eles descrevem a máquina e a execução, sem garantir desempenho em outros ambientes. Os tempos dos roteiros incluem subprocessos e não medem leitura humana nem satisfação.

Os testes exercitam a interface real de terminal, um fluxo completo de consulta, arquivos ausentes, execução fora do repositório e fim da entrada. Verificam os dois modelos, navegação relacionada, ambiguidade, filtros, privacidade dos logs, falha de gravação, registros antigos, estrutura de dados e atualização atômica. A adaptação para pt-BR acrescenta verificações de busca com e sem acentos, comandos, rótulos, avisos, ajuda e argumentos em português.

Os subprocessos de testes e demonstração declaram UTF-8 para preservar acentos no Windows, independentemente da codificação do executor. A validação também foi executada com `py -3 -X utf8`.

Os resultados esperados e obtidos ficam em `tests/results.json`, `tests/results.csv`, `tests/template_comparison.json` e `tests/usability_results.json`. A transcrição local está em `artifacts/demo_transcript.txt`; a pasta `artifacts/` é ignorada pelo Git.

O FFmpeg não estava disponível localmente; foi gerada apenas a demonstração textual. A geração de MP4 permanece disponível no GitHub Actions em Linux. Nome da equipe, RMs e publicação do vídeo no YouTube continuam pendentes.

O enunciado exige `docs/uso_ia.md` com as ferramentas utilizadas e a validação crítica. Essa declaração permanece na entrega. A aplicação usa busca e modelos de texto determinísticos, sem chamadas a modelos externos.
