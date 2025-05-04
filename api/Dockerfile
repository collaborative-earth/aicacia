# Use the official Python image as the base image
FROM python:3.10-bookworm

# Set working directory inside container
WORKDIR /app

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile* ./

# Install dependencies using pipenv
RUN pip3 install pipenv
RUN pipenv requirements > requirements.txt
RUN pip3 install -r requirements.txt

COPY server ./server

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
