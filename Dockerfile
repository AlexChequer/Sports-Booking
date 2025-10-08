FROM python:3.11-slim

COPY requirements.txt .

RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "/app/main.py"]
