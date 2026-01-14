FROM python:3.12

WORKDIR /app


COPY requirements.txt .
RUN pip install -r requirments.txt

COPY . .

EXPOSE 7777

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]




