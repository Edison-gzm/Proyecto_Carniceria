import bcrypt
from sqlalchemy.orm import Session
from app.database.models.user import User


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def create_user(self, username: str, password: str, role: str = "cajero") -> User:
        user = User(
            username=username,
            password_hash=self.hash_password(password),
            role=role,
        )
        self.session.add(user)
        self.session.commit()
        return user

    def login(self, username: str, password: str) -> User | None:
        user = self.session.query(User).filter_by(username=username, is_active=True).first()
        if user and self.verify_password(password, user.password_hash):
            return user
        return None

    def get_all_users(self) -> list[User]:
        return self.session.query(User).filter_by(is_active=True).all()

    def toggle_active(self, user_id: int) -> User:
        user = self.session.query(User).get(user_id)
        user.is_active = not user.is_active
        self.session.commit()
        return user