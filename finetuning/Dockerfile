FROM python:3.10-bookworm

WORKDIR /app

# Copy only the Pipfile and Pipfile.lock (if it exists) to the working directory
COPY Pipfile Pipfile.lock* /app/

# Install pipenv to handle environment creation
RUN pip3 install pipenv

RUN pipenv requirements > requirements.txt
RUN pip3 install -r requirements.txt

# Copy the current project files to the working directory
COPY . /app

CMD python