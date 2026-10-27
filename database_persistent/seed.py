"""Initialize the local schema and create the configured operator if absent."""

import bcrypt
from sqlalchemy import select

from business_layer.config import settings
from database_persistent.db_config import SessionLocal, create_schema
from database_persistent.models import User


def initialize_database() -> None:
    """Create tables and seed the initial admin account idempotently."""

    create_schema()
    with SessionLocal.begin() as session:
        existing_user = session.scalar(
            select(User).where(User.username == settings.admin_username)
        )
        if existing_user is None:
            password_hash = bcrypt.hashpw(
                settings.admin_password.get_secret_value().encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("ascii")
            session.add(
                User(
                    username=settings.admin_username,
                    password_hash=password_hash,
                )
            )
