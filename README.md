## Setting up server

### Prerequisite.
1. python3.10
2. pipenv
For mac -
```
brew install pipenv
```
For others -
```
pip install pipenv --user
```

### Install dependencies
```
./develop/install_deps
```

### Run server
1. add .env at the top level and add.
POSTGRES_PASSWORD=aicacia
2.
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