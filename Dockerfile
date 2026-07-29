FROM python:3.14-slim

WORKDIR /whatsapp-assistant
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .
COPY pyproject.toml .python-version uv.lock README.md ./

RUN pip install uv

RUN uv sync --no-cache

CMD ["uv", "run", "whatsapp-assistant", "--webserver", "--host", "0.0.0.0", "--port", "8000"]
