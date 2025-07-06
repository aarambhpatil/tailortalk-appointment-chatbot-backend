FROM python:3.10

COPY dev-lambda-465104-n1-91f9fc3b438c.json /
COPY *.py /
COPY .env /
COPY requirements.txt /

RUN pip install -r requirements.txt

EXPOSE 8000/tcp

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]