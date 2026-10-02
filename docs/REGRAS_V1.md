# Regras identificadas na V1

## Contas
Agência, conta, dígito e operação NÃO são fixos por banco. O conversor lê esses dados do arquivo de origem e exibe para conferência antes da exportação.

## Layouts CIGAM observados
- Santander: AG;CONTA;DIGITOD;DATA;COMPLEMENTO;DOCTO;C/D;VALOR;SALDO
- Bradesco: AG;CONTA;DIGITOD;DATA;COMPLEMENTO;DOCTO;C/D;VALOR;SALDO
- Itaú: AG;CONTA;DIGITOD;DATA;COMPLEMENTO;C/D;VALOR;SALDO
- Caixa: AG;OP;CONTA;DIGITOD;DATA;COMPLEMENTO;DOCTO;C/D;VALOR;SALDO
- BB Corrente: AG;CONTA;DIGITOD;DATA;COMPLEMENTO;DOCTO;C/D;VALOR
- BB Poupança: AG;CONTA;DIGITOD;DATA;COMPLEMENTO;C/D;VALOR

## Valores
Débito é exportado com valor negativo e C/D = D. Crédito é exportado com valor positivo e C/D = C.

## Segurança da conversão
O sistema não deve inventar dados ausentes. Quando agência/conta/dígito/operação não forem reconhecidos, a geração é bloqueada até revisão do usuário.

## Caixa
O PDF recebido é imagem (sem camada textual). A V1 usa OCR, mas o reconhecimento ainda é beta. Antes de liberar Caixa em produção, será necessário ajustar o OCR e validar contra amostras adicionais.
