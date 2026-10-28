FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RUFAS_ROOT=/opt/rufas \
    SHARED_ROOT=/workspace/shared

WORKDIR /opt/rufas

COPY RuFaS/ /opt/rufas/
RUN pip install --no-cache-dir /opt/rufas

COPY pyproject.toml /opt/project/pyproject.toml
COPY src /opt/project/src
RUN pip install --no-cache-dir /opt/project

COPY worker /opt/worker
RUN mkdir -p /workspace/shared

WORKDIR /opt

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=10 \
  CMD test -f /tmp/rufas-worker-ready

CMD ["python", "/opt/worker/main.py"]

