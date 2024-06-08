#!/bin/bash

DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_NAME="road_helper"
DB_PORT="5432"

export PGPASSWORD="$DB_PASSWORD"

execute_sql() {
    local db_name="$1"
    local sql_command="$2"
    echo "Executing SQL on $db_name: $sql_command"
    psql -h "$DB_HOST" -p $DB_PORT -U "$DB_USER" -d "$db_name" -c "$sql_command"
}

echo "Creating database: $DB_NAME"
execute_sql "postgres" "CREATE DATABASE \"$DB_NAME\";"

CREATE_MAIN_TABLE_SQL="CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    city1 VARCHAR(255) NOT NULL,
    city2 VARCHAR(255) NOT NULL,
    road VARCHAR(10) NOT NULL,
    distance INTEGER,
    is_possible BOOLEAN NOT NULL
);"

echo "Creating tables in $DB_NAME"
execute_sql "$DB_NAME" "$CREATE_MAIN_TABLE_SQL"

echo "Database and tables created successfully."
