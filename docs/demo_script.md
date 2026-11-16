# Demonstração e envio ao YouTube

A demonstração automatizada utiliza a saída real da interface de terminal. O vídeo tem legendas, não tem áudio e dura aproximadamente 110 segundos com a cena de métricas. Ele mostra consulta por tema, pergunta direta com fonte, ambiguidade de CPF e esclarecimento, entrada vazia, opção inválida, pergunta fora do escopo, três assuntos relacionados e métricas medidas, quando disponíveis. Todos os textos da demonstração são em pt-BR.

```bash
python -m unittest discover -s tests -v
python -m src.evaluation
python -m tests.run_usability
python scripts/create_demo.py --somente-texto
```

Esses comandos exigem apenas Python. A transcrição fica em `artifacts/demo_transcript.txt`. Para gerar um MP4 no Linux, instale também FFmpeg e a fonte DejaVu Sans Mono em `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf` e execute:

```bash
python scripts/create_demo.py
```

O GitHub Actions instala essas ferramentas opcionais e disponibiliza o pacote `citizen-assist-evidence`, incluindo `artifacts/citizen-assist-demo.mp4`. Baixe-o na área de artefatos da execução concluída. Uma falha na geração opcional do vídeo não pode ser apresentada como sucesso.

Para uma gravação humana de tela, execute a interface com `python src/sistema.py --sem-log`. Use as perguntas sintéticas dos roteiros, explique fonte, data e avisos, siga D02 → relacionados → S05 → relacionados → S03, mostre os relatórios reais e mencione limitações e auxílio de IA. Uma narração opcional pode explicar o agente determinístico e a comparação dos modelos de resposta. Mostre equipe e RMs após sua confirmação.

A equipe deve enviar o vídeo real pela própria conta no YouTube, selecionar a visibilidade Não listado, verificar a URL em um navegador sem autenticação e inseri-la no README e em `SUBMISSION_LINKS.TXT`. Não há conta conectada nem ferramenta de envio ao YouTube disponível nesta sessão. Não utilize um endereço provisório como evidência de publicação. O MP4 é uma demonstração por roteiro, sem estudo humano de usabilidade.
