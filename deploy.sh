#!/bin/bash

# Sai do script se ocorrer um erro
set -e  

cd src

# Instalar dependências do projeto
pip install -r requirements.txt

# Coletar arquivos estáticos (sem pedir confirmação)
python manage.py collectstatic --noinput

# Aplicar migrações do banco de dados
python manage.py migrate
