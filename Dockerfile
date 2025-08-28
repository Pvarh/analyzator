FROM python:3.10-slim

WORKDIR /app

# Systémové závislosti
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python závislosti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírovanie aplikácie
COPY . .

# Vytvorenie potrebných priečinkov
RUN mkdir -p data/raw data/studio auth logs

# Vytvorenie sessions.json z template ak neexistuje
RUN if [ ! -f auth/sessions.json ]; then cp auth/sessions.template.json auth/sessions.json; fi

# Nastavenie oprávnení
RUN chmod +x /app/*.py

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]