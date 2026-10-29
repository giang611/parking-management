"""Repository SQLAlchemy triển khai giao diện truy cập tài khoản."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from business_layer.services.repository_ports import UserCredentials, UserRepositoryPort
from database_persistent.models import User


class SqlAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, session: Session):
        self._session = session

    def get_by_username(self, username: str) -> UserCredentials | None:
        user = self._session.scalar(select(User).where(User.username == username))
        if user is None:
            return None
        return UserCredentials(username=user.username, password_hash=user.password_hash)
