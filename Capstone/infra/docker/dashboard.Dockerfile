FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir streamlit
COPY . .
CMD ["streamlit", "run", "dashboard/streamlit_app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

