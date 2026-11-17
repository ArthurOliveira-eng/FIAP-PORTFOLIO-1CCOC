# Interface web: integração e validação

A implementação usa os modelos Consulta e Menu de temas fornecidos pelo responsável pelo projeto. Preserva fundo cinza, superfícies claras, destaque laranja, fonte Inter, ícones, cartões e navegação. Os textos vêm da base real; quantidades, histórico e resultados não são exemplos simulados. A interface de terminal permanece disponível.

O servidor usa `ThreadingHTTPServer`, a biblioteca padrão e os componentes existentes. Os recursos estáticos são explicitamente permitidos. As rotas `GET /api/estado`, `/api/base` e `/api/indicadores` retornam dados do projeto; `POST /api/consultar` recebe `sid`, `texto`, `modelo`, `tema` opcional e `reiniciar` opcional. A resposta inclui o texto integral produzido pelo agente, estado, registros, fontes, assuntos relacionados e latência. O backend limita as sessões a 50; uma sessão descartada reinicia seu contexto na próxima consulta.

Os controles incluem seleção de tema, busca, abertura por ID, assuntos relacionados, nova consulta, fontes, apoio comunitário, histórico, busca no histórico, indicadores, seleção de modelo, redução de animações e notificações. O histórico fica somente na memória da aba. O ditado opcional solicita confirmação e permissão de microfone e pode usar transcrição online pelo navegador. Apenas o texto revisado é enviado ao servidor local para pesquisa. A preferência claro/escuro é persistida; consultas e notificações não são persistidas.

Entrada no painel direito, lupa superior, modo escuro persistido, contador de notificações, transcrição simulada e permissão negada foram verificados com `python scripts/test_web_inputs.py`. O reconhecimento de áudio real depende do microfone, do navegador e da disponibilidade de seu serviço; não foi validado com a voz do usuário. O teste automatizado simula os eventos da API de voz e valida o fluxo até a consulta real na base.

## Verificações realizadas

A atualização visual baseada nos prints e no vídeo acrescentou pressão/retorno dos botões, revelação progressiva de palavras, pergunta à direita e tela exclusiva de Conversas. A seleção, a busca e a limpeza do histórico foram verificadas no navegador em desktop e celular. A transcrição progressiva foi verificada com eventos simulados de voz, sem capturar áudio do usuário. Nenhuma onda de clique foi adicionada; os efeitos respeitam a redução de movimento.

- 30 testes Python aprovados, incluindo os contratos existentes e sete testes da camada HTTP.
- Consulta de recuperação de senha, navegação por Documentos e CIN, ambiguidade de CPF e abertura dos cinco painéis auxiliares verificados no Edge.
- Troca de modelo A/B no painel de configurações e requisições isoladas entre sessões verificadas.
- Erros de sessão, tema, modelo, JSON e entradas longas verificados por HTTP.
- Falha de conexão simulada no navegador: mensagem explícita, sem resposta fictícia.
- Capturas de tela em 1200 × 760 e 390 × 844; sem transbordamento horizontal na largura de celular.
- Chat independente com várias mensagens por conversa, novas sessões isoladas, retomada sem nova requisição e passagem para voz preservando a sessão.
- Falha de rede no chat com opção de tentar novamente, sem trocar de tela.
- Painel de conversas dentro da janela em 1920 × 1080, 1366 × 768, 1024 × 768, 768 × 1024 e 390 × 844; campo de envio visível e rolagem interna das mensagens.
- Módulos JavaScript e estilos separados carregados pelo servidor com tipos corretos; tentativas de acesso fora dos recursos permitidos retornam 404.
- Tipos inválidos nos pedidos e corpos acima de 8 KiB rejeitados de forma controlada.

Para repetir os testes de backend:

```bash
python -m unittest discover -s tests -v
```

Para repetir a verificação opcional de navegador, com servidor local iniciado, instale Playwright no ambiente de desenvolvimento e utilize o Microsoft Edge:

```bash
python -m pip install playwright
python scripts/test_web_browser.py
python scripts/test_web_inputs.py
python scripts/test_web_chat.py
```

Playwright não é dependência para executar a aplicação. As capturas ficam em `artifacts/`, ignorado pelo Git. Esses testes não substituem um estudo de acessibilidade ou usabilidade com participantes humanos.
