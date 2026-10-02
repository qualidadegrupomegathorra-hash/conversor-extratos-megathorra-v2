@echo off
setlocal
cd /d "%~dp0"
title Instalador OCR Caixa - MegaThorra

echo ================================================
echo  Instalacao unica do OCR para extratos da Caixa
echo ================================================
echo.

where winget >nul 2>nul
if errorlevel 1 (
  echo O Windows Package Manager ^(winget^) nao foi encontrado.
  echo Instale o Tesseract OCR para Windows ^(UB-Mannheim^) e depois execute INICIAR.bat.
  pause
  exit /b 1
)

echo Instalando Tesseract OCR...
winget install --id UB-Mannheim.TesseractOCR --exact --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
  echo.
  echo A instalacao nao foi concluida. Tente novamente com permissao de administrador.
  pause
  exit /b 1
)

echo.
echo Instalacao concluida.
echo Feche esta janela e execute INICIAR.bat.
pause
