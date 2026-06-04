@echo off
REM Script de conveniencia para rodar servidor e cliente no Windows

if "%1"=="server" goto server
if "%1"=="servidor" goto server
if "%1"=="client" goto client
if "%1"=="cliente" goto client

echo Uso: run.bat [server^|client]
echo   server  - Inicia o servidor FastAPI
echo   client  - Inicia o cliente de sincronizacao
exit /b 1

:server
echo Iniciando servidor...
python -m uvicorn servidor.main:app --host 0.0.0.0 --port 8000 --reload
goto end

:client
echo Iniciando cliente...
python -m cliente.client
goto end

:end
