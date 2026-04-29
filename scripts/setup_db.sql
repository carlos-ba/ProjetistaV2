-- Execute este script conectado como superusuário (postgres) no pgAdmin ou psql
-- Cria o usuário e banco de dados para o ProjetistaV2

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'projetista') THEN
        CREATE USER projetista WITH PASSWORD 'projetista';
    END IF;
END
$$;

CREATE DATABASE projetista_v2 OWNER projetista;

GRANT ALL PRIVILEGES ON DATABASE projetista_v2 TO projetista;
