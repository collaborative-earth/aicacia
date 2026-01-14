# package: aicacia-db

Manages the migrations and models in the Aicacia DB.


> import as: `from db import ..`

## Commands
`pipenv --python 3.10`
`pip install -e ../core   -e ../other-localDependencies`
`pipenv install ..`
`pipenv install --dev pytest ..`


From root
`alembic -c db/alembic.ini check` or `uv run --project db alembic -c db/alembic.ini check`

