# Manutenção da base de conhecimento

Os registros ficam em `data/knowledge_base.json`. A aplicação lê esse arquivo na inicialização; alterar dados não exige reescrever as regras de busca.

Cada registro contém `id`, `theme`, `question`, `keywords`, `summary_guidance`, `reference`, `verification_date`, `confirmation_warning` e `related_ids`. Os nomes dos campos são identificadores técnicos estáveis; seus textos devem ser escritos em português brasileiro.

1. Abra a fonte oficial e confira o escopo, os documentos, as condições de acesso e os avisos. Não deduza taxas, prazos ou decisões individuais.
2. Redija uma orientação curta e clara em pt-BR. Registre a data real da revisão em `verification_date`, no formato `AAAA-MM-DD`.
3. Use um ID único e um tema existente ou um novo tema revisado. Novos temas aparecem automaticamente no menu, pela ordem dos registros.
4. Adicione palavras-chave relevantes em português e IDs relacionados existentes. Evite ligações ao próprio registro.
5. Valide a base e execute os testes, a avaliação A/B e os roteiros de uso.

Para manutenção administrativa, utilize `save_record(caminho, registro)` para adicionar e `save_record(caminho, registro, replace=True)` para corrigir. A função valida o conjunto inteiro antes de gravar um arquivo temporário e substituir a base de forma atômica no mesmo sistema de arquivos. Se a validação falhar, o arquivo anterior é preservado. Essa função não está exposta na interface do cidadão.

A validação rejeita lista vazia, campos ausentes, tipos incorretos, textos vazios, palavras-chave vazias, valores duplicados, IDs inválidos, URLs que não sejam HTTPS do domínio gov.br, credenciais embutidas na URL, portas inadequadas, datas futuras e referências inexistentes ou ao próprio registro. A forma da URL não garante a veracidade da fonte nem sua disponibilidade.

```bash
python -m unittest discover -s tests -v
python -m src.evaluation
python -m tests.run_usability
```

Arquivos ausentes, vazios ou malformados produzem uma mensagem controlada: restaure uma base válida. Modelos de resposta ausentes ou malformados impedem respostas inseguras. Falhas ao gravar logs mostram um aviso, mantendo a orientação disponível. Use `--sem-log` para não armazenar telemetria. A aplicação requer Python 3.10 ou superior; no Windows, pode-se usar `py -3`.
