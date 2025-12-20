#!/bin/bash
# Run from root directory, but use Pipfile from api/
cd "$(dirname "$0")"
PIPENV_PIPFILE=api/Pipfile pipenv run alembic -c alembic.ini "$@"

