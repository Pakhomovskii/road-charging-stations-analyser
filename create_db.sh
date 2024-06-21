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

    if [ "$db_name" = "postgres" ] && [ "$sql_command" = "CREATE DATABASE IF NOT EXISTS \"$DB_NAME\";" ]; then
        if ! psql -h "$DB_HOST" -p $DB_PORT -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
            psql -h "$DB_HOST" -p $DB_PORT -U "$DB_USER" -c "CREATE DATABASE \"$DB_NAME\";"
        else
            echo "Database $DB_NAME already exists"
        fi
    else
        if ! psql -h "$DB_HOST" -p $DB_PORT -U "$DB_USER" -d "$db_name" -c "$sql_command" 2>&1; then
            echo "ERROR: $(psql -h "$DB_HOST" -p $DB_PORT -U "$DB_USER" -d "$db_name" -c "$sql_command" 2>&1)"
            exit 1
        fi
    fi
}

echo "Creating database: $DB_NAME"
execute_sql "postgres" "CREATE DATABASE IF NOT EXISTS \"$DB_NAME\";"

CREATE_MAIN_TABLE_SQL="CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    city1 VARCHAR(255) NOT NULL,
    city2 VARCHAR(255) NOT NULL,
    road VARCHAR(10) NOT NULL,
    is_possible BOOLEAN NOT NULL,
    problem_point1 VARCHAR(255),
    problem_point2 VARCHAR(255)
);"

echo "Creating tables in $DB_NAME"
execute_sql "$DB_NAME" "$CREATE_MAIN_TABLE_SQL"

echo "Database and tables created successfully."
