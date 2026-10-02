@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Conversor de Extratos MegaThorra v1.4.1

echo ================================================
echo  Conversor de Extratos MegaThorra - v1.4.1
echo ================================================
echo.

if not exist .venv (
  echo [1/4] Criando ambiente Python...
  py -m venv .venv
  if errorlevel 1 goto :erro_python
)
call .venv\Scripts\activate

echo [2/4] Instalando/atualizando bibliotecas...
python -m pip install -r requirements.txt
if errorlevel 1 goto :erro_python

echo [3/4] Localizando leitor OCR da Caixa...
set "TESSERACT_CMD="
for /f "usebackq delims=" %%I in (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0localizar_tesseract.ps1" 2^>nul`) do (
  if not defined TESSERACT_CMD set "TESSERACT_CMD=%%I"
)

if defined TESSERACT_CMD (
  for %%I in ("%TESSERACT_CMD%") do set "PATH=%%~dpI;%PATH%"
  echo OCR da Caixa: OK.
  echo Localizado em: %TESSERACT_CMD%
) else (
  echo.
  echo AVISO: Tesseract OCR nao foi localizado.
  echo Os demais bancos continuam funcionando normalmente.
  echo Para usar a Caixa, execute uma unica vez o arquivo INSTALAR_OCR_CAIXA.bat
  echo e depois abra novamente o INICIAR.bat.
  echo.
)

echo [4/4] Abrindo o sistema...
streamlit run app.py
pause
exit /b 0

:erro_python
echo.
echo Nao foi possivel preparar o ambiente Python.
echo Verifique se o Python esta instalado e se ha conexao com a internet.
echo.
pause
exit /b 1
