FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace/src

WORKDIR /workspace

COPY requirements/notebook.txt /tmp/notebook-requirements.txt
COPY requirements/dev.txt /tmp/dev-requirements.txt
RUN pip install --no-cache-dir \
    -r /tmp/notebook-requirements.txt \
    -r /tmp/dev-requirements.txt

COPY pyproject.toml /workspace/project/pyproject.toml
COPY src /workspace/project/src
RUN pip install --no-cache-dir /workspace/project

COPY notebooks /workspace/notebooks
COPY configs /workspace/configs
COPY RuFaS/input/data/feed/NASEM_Comp_with_TDN.csv /workspace/data/NASEM_Comp_with_TDN.csv

RUN mkdir -p /workspace/shared

EXPOSE 8888

HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=10 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8888/lab', timeout=3)"

CMD ["sh", "-c", "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --ServerApp.token=${JUPYTER_TOKEN} --ServerApp.allow_origin='*' --notebook-dir=/workspace"]

