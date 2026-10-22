#!/bin/sh
set -eu

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=app_password="$APP_DATABASE_PASSWORD" \
  --set=migration_password="$MIGRATION_DATABASE_PASSWORD" <<'SQL'
CREATE ROLE app_user LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE migration_user LOGIN PASSWORD :'migration_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
GRANT CONNECT ON DATABASE guetteur TO app_user, migration_user;
GRANT USAGE, CREATE ON SCHEMA public TO migration_user;
GRANT USAGE ON SCHEMA public TO app_user;
SQL
