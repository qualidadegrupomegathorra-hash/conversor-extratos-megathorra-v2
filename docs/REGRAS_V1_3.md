# Regras V1.3 — Itaú

Validação feita com o extrato original e o arquivo importado manualmente no CIGAM.

- Leitura XLSX em modo normal (não read-only) porque alguns arquivos Itaú possuem dimensão interna incorreta e, em modo read-only, apenas as primeiras linhas eram visíveis.
- Agência e conta continuam sendo lidas de cada extrato.
- A conta é enviada ao CIGAM sem zeros à esquerda.
- O dígito é mantido em coluna separada.
- Linhas com saldo e sem valor recebem VALOR=0 e C/D=C, preservando o saldo.
- Débitos permanecem negativos e recebem C/D=D.
- Créditos permanecem positivos e recebem C/D=C.
- O histórico é preservado como no arquivo de origem, inclusive espaços internos.
