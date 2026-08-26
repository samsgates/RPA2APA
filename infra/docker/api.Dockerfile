FROM python:3.12-slim
WORKDIR /workspace
COPY apps/api /workspace/apps/api
RUN pip install --no-cache-dir -e /workspace/apps/api
COPY examples /workspace/examples
WORKDIR /workspace/apps/api
CMD ["uvicorn","rpa2apa_api.main:app","--host","0.0.0.0","--port","8080"]
