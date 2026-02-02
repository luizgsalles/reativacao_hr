@echo off
chcp 65001 >nul
cls

echo.
echo ================================================================================
echo   INSTALADOR - Sistema de Reativacao de Clientes
echo ================================================================================
echo.
echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: Python nao foi encontrado!
    echo.
    echo Por favor, instale Python 3.9+ de: https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo OK - Python instalado!
echo.
echo Instalando dependencias...
pip install -q -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERRO ao instalar dependencias!
    echo.
    pause
    exit /b 1
)

cls

echo.
echo ================================================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo ================================================================================
echo.
echo Proximas instrucoes:
echo.
echo 1. Clique 2x em "run_final.bat" para abrir o dashboard
echo.
echo 2. O navegador abra em http://localhost:8501
echo.
echo 3. Leia "Leia_Primeiro.txt" para instrucoes de uso
echo.
echo ================================================================================
echo.
pause
