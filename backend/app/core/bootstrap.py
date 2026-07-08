import logging
import os

from sqlalchemy.orm import Session

from ..models import Admin, User, UserProfile
from .defaults import create_default_categories
from .security import get_password_hash

logger = logging.getLogger(__name__)


def bootstrap_initial_admin(db: Session) -> None:
    email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin123!")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id, first_name="System", last_name="Admin"))
        create_default_categories(db, user.id)

    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        db.add(
            Admin(
                email=email,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=True,
            )
        )

    db.commit()
    logger.info("Initial admin available: %s", email)

