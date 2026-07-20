FROM python:3.14-slim

WORKDIR /whatsapp-assistant
COPY src ./src
COPY pyproject.toml .python-version uv.lock README.md ./

RUN pip install uv

RUN uv sync --no-cache

CMD ["uv", "run", "fastapi", "run", "src/whatsapp_assistant/main.py", "--host", "0.0.0.0", "--port", "8000"]