import bcrypt
from sqlalchemy.orm import Session
from database.models.user import User, UserRole
 
 
class AuthService:
    def __init__(self, session: Session):
        self.session = session
 
    def login(self, username: str, password: str) -> User | None:
        user = self.session.query(User).filter_by(username=username, is_active=True).first()
        if not user:
            return None
        if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return user
        return None
 
    def create_user(self, username: str, password: str, full_name: str, role: UserRole) -> User:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(username=username, password_hash=password_hash, full_name=full_name, role=role)
        self.session.add(user)
        self.session.commit()
        return user
 
    def change_password(self, user_id: int, new_password: str) -> bool:
        user = self.session.get(User, user_id)
        if not user:
            return False
        user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        self.session.commit()
        return True
 
    def toggle_active(self, user_id: int) -> bool:
        user = self.session.get(User, user_id)
        if not user:
            return False
        user.is_active = not user.is_active
        self.session.commit()
        return user.is_active
 
    def get_all(self) -> list[User]:
        return self.session.query(User).order_by(User.username).all()