FROM python:3.11

RUN pip install --upgrade pip

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY ./app /app

WORKDIR /app

# Install uvicorn
RUN pip install uvicorn

# Start the FastAPI application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]