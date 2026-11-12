FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV DJANGO_SETTINGS_MODULE=config.settings

ARG SECRET_KEY=placeholder-for-build
ARG DATABASE_URL=sqlite:////tmp/build.db
ARG ALLOWED_HOSTS=localhost

RUN SECRET_KEY=$SECRET_KEY DATABASE_URL=$DATABASE_URL \
    ALLOWED_HOSTS=$ALLOWED_HOSTS \
    uv run python manage.py collectstatic --noinput

EXPOSE 8080

# 1 worker + wątki: maszyna ma 1 vCPU, a drugi worker duplikował pamięć importową.
# --preload ładuje aplikację raz w masterze, workery dziedziczą ją przez copy-on-write.
CMD ["uv", "run", "gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "1", \
     "--threads", "4", \
     "--preload", \
     "--timeout", "30", \
     "--access-logfile", "-"]
