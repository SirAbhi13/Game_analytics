#!/bin/sh

set -e

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Execute the command passed as arguments to the entrypoint
exec "$@"
