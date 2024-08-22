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
Add `.env` at the top level and add the following
`POSTGRES_PASSWORD=aicacia`

```
./develop/run_dev_server
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
