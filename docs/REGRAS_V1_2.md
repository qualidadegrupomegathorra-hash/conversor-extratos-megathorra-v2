# Regras V1.2

## Bradesco CSV

1. Ler agência e conta do cabeçalho do próprio extrato.
2. Considerar o primeiro bloco `Data;Lançamento;Dcto.;Crédito (R$);Débito (R$);Saldo (R$)` como o período principal.
3. Encerrar a leitura na primeira linha `Total`.
4. Ignorar a seção `Últimos Lançamentos` e qualquer bloco posterior, pois pode conter movimentos de meses diferentes do período solicitado.
5. Manter `SALDO ANTERIOR` com valor 0 e C/D = C.
6. Créditos = C com valor positivo; débitos = D com valor negativo.
7. Não fixar agência, conta ou dígito no código.
