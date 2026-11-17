# Interface web: integração e validação

A implementação usa os modelos Consulta e Menu de temas fornecidos pelo responsável pelo projeto. Preserva fundo cinza, superfícies claras, destaque laranja, fonte Inter, ícones, cartões e navegação. Os textos vêm da base real; quantidades, histórico e resultados não são exemplos simulados. A interface de terminal permanece disponível.

O servidor usa `ThreadingHTTPServer`, a biblioteca padrão e os componentes existentes. Os recursos estáticos são explicitamente permitidos. As rotas `GET /api/estado`, `/api/base` e `/api/indicadores` retornam dados do projeto; `POST /api/consultar` recebe `sid`, `texto`, `modelo`, `tema` opcional e `reiniciar` opcional. A resposta inclui o texto integral produzido pelo agente, estado, registros, fontes, assuntos relacionados e latência. O backend limita as sessões a 50; uma sessão descartada reinicia seu contexto na próxima consulta.

Os controles incluem seleção de tema, busca, abertura por ID, assuntos relacionados, nova consulta, fontes, apoio comunitário, histórico, busca no histórico, indicadores, seleção de modelo, redução de animações e notificações. O histórico fica somente na memória da aba. A interface não solicita microfone nem transmite consultas a serviços externos.

## Verificações realizadas

- 27 testes Python aprovados, incluindo os contratos existentes e quatro testes da camada HTTP.
- Consulta de recuperação de senha, navegação por Documentos e CIN, ambiguidade de CPF e abertura dos cinco painéis auxiliares verificados no Edge.
- Troca de modelo A/B no painel de configurações e requisições isoladas entre sessões verificadas.
- Erros de sessão, tema, modelo, JSON e entradas longas verificados por HTTP.
- Falha de conexão simulada no navegador: mensagem explícita, sem resposta fictícia.
- Capturas de tela em 1200 × 760 e 390 × 844; sem transbordamento horizontal na largura de celular.

Para repetir os testes de backend:

```bash
python -m unittest discover -s tests -v
```

Para repetir a verificação opcional de navegador, com servidor local iniciado, instale Playwright no ambiente de desenvolvimento e utilize o Microsoft Edge:

```bash
python -m pip install playwright
python scripts/test_web_browser.py
```

Playwright não é dependência para executar a aplicação. As capturas ficam em `artifacts/`, ignorado pelo Git. Esses testes não substituem um estudo de acessibilidade ou usabilidade com participantes humanos.
