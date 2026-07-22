FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	UV_PROJECT_ENVIRONMENT=/app/.venv \
	PATH="/app/.venv/bin:$PATH"

# Use a custom browser User-Agent to bypass potential host/VPN/proxy filters that block default Debian APT requests
RUN apt-get -o Acquire::http::User-Agent=Mozilla/5.0 update \
 && apt-get -o Acquire::http::User-Agent=Mozilla/5.0 install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen --no-dev --no-install-project

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
