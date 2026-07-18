#!/bin/bash
# Only runs on first container init (empty data volume). POSTGRES_DB already
# creates the main "whatsapp_assistant" database; this creates the second,
# separate database used solely by ADK's DatabaseSessionService.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE agent_sessions;
EOSQL
