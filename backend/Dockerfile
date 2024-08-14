FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
RUN sed -i 's/\r$//g' entrypoint.sh
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]

