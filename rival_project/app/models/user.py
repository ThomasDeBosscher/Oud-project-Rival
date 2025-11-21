from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'app_user'

    id = db.Column('user_id', db.BigInteger, primary_key=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    # watchlist_items relationship provided from Watchlist backref

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles: str) -> bool:
        if not self.role:
            return False
        return self.role in roles