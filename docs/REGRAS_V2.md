# Conversor de Extratos MegaThorra — V2

## Objetivo
Interface operacional para a equipe de Conciliação Bancária converter os formatos bancários homologados para os layouts de importação do CIGAM.

## Princípios preservados
- Nenhuma agência, conta, dígito ou operação fica fixa por banco.
- O arquivo atual é invalidado quando o usuário troca de banco ou inicia nova conversão.
- Os parsers homologados da V1.4.1 foram preservados sem mudança de regra financeira.
- Nenhum CSV é liberado se faltarem campos obrigatórios de identificação.
- O arquivo gerado mantém UTF-8 com BOM e separador `;`.

## Bancos homologados
- Santander — XLSX
- Bradesco — CSV
- Itaú — XLSX
- Caixa — PDF com OCR
- Banco Brasil Corrente — PDF
- Banco Brasil Poupança — PDF

## Melhorias da V2
- Interface executiva/corporativa.
- Fluxo em quatro etapas: Origem, Conferência, Validação e Exportação.
- Indicadores de quantidade, créditos, débitos, movimento líquido e período.
- Pré-visualização de até 500 registros.
- Resumo do arquivo antes do download.
- Mensagens de erro simplificadas para o usuário.


## Correção V2.2 — Caixa
- Preserva todos os registros visuais detectados no layout homologado da Caixa.
- Usa a natureza `C`/`D` do próprio lançamento quando disponível no OCR.
- `C` sempre gera valor positivo; `D` sempre gera valor negativo.
- `SALDO DIA` gera documento `0`, C/D vazio e valor `0`.
- Remove zeros à esquerda dos documentos.
- Corrige OCR de valores monetários com pontuação quebrada, como `2.99430` e `13,594.34`.
- Faz uma segunda tentativa de OCR somente nas linhas que falharem na primeira leitura.
- Recalcula saldos a partir do saldo mais recente e da sequência dos lançamentos, evitando contaminar todo o extrato com um saldo final OCR incorreto.
- Não altera os parsers dos demais bancos.
