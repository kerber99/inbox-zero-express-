@echo off
:: Navega até a pasta do projeto para garantir que o .env seja lido corretamente
cd /d C:\Users\emilly.kerber\inbox-zero-express
:: Executa o robô usando o pythonw (versão do Python que roda sem abrir janela no Windows)
start "" pythonw robo_inbox.py
