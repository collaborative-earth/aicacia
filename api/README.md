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
Add `.env` inside `server` and add the following
`POSTGRES_PASSWORD=aicacia`

```
./develop/run_dev_server
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
