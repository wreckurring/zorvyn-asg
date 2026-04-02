from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserProfileUpdate
from app.services.auth_service import hash_password, verify_password


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_all_users(db: Session) -> list[User]:
    return db.query(User).all()


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.viewer,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_role(db: Session, user: User, role: UserRole) -> User:
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def update_user_status(db: Session, user: User, is_active: bool) -> User:
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(db: Session, user: User, data: UserProfileUpdate) -> tuple[User, str | None]:
    error = None

    if data.new_password:
        if not data.current_password:
            return user, "current_password is required to set a new password"
        if not verify_password(data.current_password, user.hashed_password):
            return user, "Current password is incorrect"
        user.hashed_password = hash_password(data.new_password)

    if data.email:
        user.email = data.email

    db.commit()
    db.refresh(user)
    return user, error
