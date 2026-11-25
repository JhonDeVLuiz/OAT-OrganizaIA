@echo off
rem ============================================================
rem  Compila o OrganizaIA em UM UNICO .exe (modo arquivo unico)
rem  Basta dar dois cliques neste arquivo no Windows 11.
rem ============================================================
title Compilando OrganizaIA...
cd /d "%~dp0"

echo.
echo  [1/5] Verificando ambiente virtual (.venv)...
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  ERRO: a pasta .venv nao foi encontrada junto deste script.
    echo  Coloque este arquivo .bat na raiz do projeto OrganizaIA.
    echo.
    pause
    exit /b 1
)

echo  [2/5] Garantindo que o PyInstaller esta instalado...
".venv\Scripts\python.exe" -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo        Instalando PyInstaller...
    ".venv\Scripts\python.exe" -m pip install pyinstaller
    if errorlevel 1 (
        echo  ERRO: nao foi possivel instalar o PyInstaller. Verifique sua internet.
        pause
        exit /b 1
    )
)

echo  [3/5] Salvando copia de seguranca dos dados do programa antigo...
if exist "dist\dados" xcopy "dist\dados" "_backup_dist\dados\" /e /i /y >nul
if exist "dist\organizados" xcopy "dist\organizados" "_backup_dist\organizados\" /e /i /y >nul
if exist "dist\logs" xcopy "dist\logs" "_backup_dist\logs\" /e /i /y >nul

echo  [4/5] Compilando o arquivo unico ^(isto pode levar 3 a 6 minutos^)...
".venv\Scripts\python.exe" -m PyInstaller --clean -y OrganizaIA.spec
if errorlevel 1 (
    echo.
    echo  ERRO: a compilacao falhou. role a janela acima para ver o motivo.
    echo.
    pause
    exit /b 1
)

if not exist "dist\OrganizaIA.exe" (
    echo  ERRO: o arquivo dist\OrganizaIA.exe nao foi criado.
    pause
    exit /b 1
)

echo  [5/5] Restaurando dados ao lado do exe...
if not exist "dist\entrada" mkdir "dist\entrada"
if exist "_backup_dist\dados" xcopy "_backup_dist\dados" "dist\dados\" /e /i /y >nul
if exist "_backup_dist\organizados" xcopy "_backup_dist\organizados" "dist\organizados\" /e /i /y >nul
if exist "_backup_dist\logs" xcopy "_backup_dist\logs" "dist\logs\" /e /i /y >nul

echo.
echo  ============================================================
echo   PRONTO! O programa e UM UNICO ARQUIVO:
echo.
echo   dist\OrganizaIA.exe
echo.
echo   Esse exe funciona sozinho em qualquer Windows 10/11
echo   (nao precisa mais copiar pasta nenhuma).
echo   Na primeira execucao ele cria .env, entrada, dados e
echo   logs na mesma pasta onde estiver.
echo   Copia de seguranca dos dados antigos: pasta "_backup_dist"
echo  ============================================================
echo.
start "" explorer "dist"
pause
