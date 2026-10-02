# V1.4 — Leitor Caixa PDF

## Alterações
- Leitura do PDF de imagem da Caixa por OCR com detecção visual das linhas de lançamento.
- Agência, operação, conta e dígito são lidos do próprio extrato; não ficam fixos no sistema.
- O OCR é executado apenas sobre as faixas de lançamentos, reduzindo erros de cabeçalho/rodapé.
- Descrições da Caixa são normalizadas para o padrão validado no CIGAM.
- Valores de débito permanecem negativos e créditos positivos.
- O saldo é validado/reconstruído pela sequência do próprio extrato: saldo atual = saldo da linha anterior no tempo + valor.
- `INICIAR.bat` tenta localizar ou instalar Tesseract OCR automaticamente no Windows.
- A interface deixa de exibir traceback técnico ao usuário final.

## Amostra de validação
Referência utilizada no desenvolvimento: Extrato por período da Caixa de 01/04/2026 a 30/04/2026, 17 páginas.
Resultado esperado da amostra: 515 lançamentos no layout CIGAM Caixa.
