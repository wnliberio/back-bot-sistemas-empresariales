FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
ENV STREAMLIT_SERVER_HEADLESS=true
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]