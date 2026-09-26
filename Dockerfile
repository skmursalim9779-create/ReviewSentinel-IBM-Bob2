FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .
ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000
CMD ["reviewsentinel-web"]
