# Conversor de Extratos MegaThorra — V2

Aplicação da Conciliação Bancária para converter extratos homologados no layout de importação do CIGAM.

## Como iniciar no Windows
1. Descompacte a pasta.
2. Execute `INICIAR.bat`.
3. Aguarde o navegador abrir em `http://localhost:8501`.
4. Escolha o banco, envie o arquivo, confira conta/período/totais e baixe o CSV.

## Bancos e formatos homologados
- Santander: XLSX/XLSM
- Bradesco: CSV
- Itaú: XLSX/XLSM
- Caixa: PDF (OCR/Tesseract)
- Banco Brasil Corrente: PDF
- Banco Brasil Poupança: PDF

## Caixa / OCR
A Caixa requer o Tesseract OCR. O `INICIAR.bat` tenta localizar instalações existentes. Se necessário, utilize `INSTALAR_OCR_CAIXA.bat` uma única vez.

## Segurança operacional
- Ao trocar de banco, o upload anterior é invalidado.
- Agência/conta/dígito/operação vêm do extrato e podem ser conferidos na tela.
- O CSV só é liberado quando os campos obrigatórios estão preenchidos.

## Publicação por link
A aplicação é compatível com hospedagem Streamlit. Para uso corporativo por link, recomenda-se publicar em ambiente controlado pela empresa e definir autenticação/acesso antes da liberação aos usuários.


### Caixa — correção V2.2
A versão 2.2 corrige a leitura do extrato PDF da Caixa, principalmente perda de lançamentos, identificação C/D, sinais dos valores, documentos com zeros à esquerda e saldos contaminados por OCR. O layout de exportação CIGAM permanece `AG;OP;CONTA;DIGITOD;DATA;COMPLEMENTO;DOCTO;C/D;VALOR;SALDO`.
