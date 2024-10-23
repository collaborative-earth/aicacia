# Aicacia API

## Setting up API server in local

### Prerequisite
1. python3.10
2. pipenv
3. Docker

Pipenv Installation -
```
brew install pipenv
```
or
```
pip install pipenv --user
```

### Install dependencies
```
./develop/install_deps
```

### Run server
Add `.env` inside `api` and add the following
`POSTGRES_PASSWORD=aicacia`

Run server
```
./develop/run_dev_server
```

Create tables for the first time.
```
pipenv run alembic upgrade head
```


### To Add or update python dependency

Run the following and commit the `pipfile` and `pipfile.lock` changes.
```
pipenv upgrade <package_name>
```


### To change database schema
1. Change the model in models.py.
2. Create a migration.
```
./create_db_migration "<message>"
```
3. Run the migration.
```
pipenv run alembic upgrade head
```

### To upload aicacia-document-exporter sqlite result files to PostgreSQL db:

Run the following Python script:
```
python3 develop/upload_sqlite_data.py <folder_with_db_files> --db_pass <your_postgres_password>
```
For full argument list use:
```
python3 develop/upload_sqlite_data.py --help
```
To test the upload of sample data to your local db:
```
python3 develop/upload_sqlite_data.py ./develop/sample_data --db_pass aicacia
```
Make sure to truncate the tables if you wish to upload same documents again. 