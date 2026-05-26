FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV SECRET_KEY=placeholder-for-build \
    DJANGO_SETTINGS_MODULE=config.settings \
    DATABASE_URL=sqlite:////tmp/build.db \
    ALLOWED_HOSTS=localhost

RUN uv run python manage.py collectstatic --noinput

EXPOSE 8080

CMD ["uv", "run", "gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "1", \
     "--timeout", "30", \
     "--access-logfile", "-"]
