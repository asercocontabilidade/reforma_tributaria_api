# alembic/env.py
from __future__ import annotations
import os, sys
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# 1) Garanta que o Python ache o diretório do projeto e o /src
HERE = os.path.dirname(__file__)                 # .../alembic
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 2) Carrega variáveis de ambiente
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

# 3) Importe Base e os MODELOS ORM (não entidades Pydantic)
from infrastructure.database import Base, DATABASE_URL
# IMPORTANTE: importe todos os módulos que definem tabelas,
# para que elas sejam registradas no Base.metadata:
from src.domain.entities.user_entity import RoleType, User# <--- ESTE é o modelo ORM

# 4) Config Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = os.getenv("DATABASE_URL", DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_name=None,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    url = os.getenv("DATABASE_URL", DATABASE_URL)
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

