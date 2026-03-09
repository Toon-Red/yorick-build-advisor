FROM python:3.12-slim

WORKDIR /app

# Only pytest needed — all test deps are stdlib or project-local
RUN pip install --no-cache-dir pytest

COPY . .

CMD ["python", "-m", "pytest", "tests/", "-v"]
