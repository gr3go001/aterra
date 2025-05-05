FROM python:3.12-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar as dependências e instalar
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da aplicação
COPY . ./

# Expor a porta que a aplicação usará
EXPOSE 8000

# Comando de inicialização via Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
