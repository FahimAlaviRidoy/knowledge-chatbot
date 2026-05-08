"""
Simple in-memory user store.
For production: replace with SQLAlchemy + PostgreSQL/SQLite.
"""
from datetime import datetime
from typing import Optional, Dict
import uuid
from app.core.security import hash_password
from app.core.logger import log


class UserDB:
    def __init__(self):
        self._users: Dict[str, dict] = {}
        self._by_username: Dict[str, str] = {}  # username -> id
        # Seed a default admin
        self._seed_admin()

    def _seed_admin(self):
        admin_id = str(uuid.uuid4())
        admin = {
            "id": admin_id,
            "username": "admin",
            "email": "admin@knowledgebot.local",
            "hashed_password": hash_password("admin1234"),
            "role": "admin",
            "created_at": datetime.utcnow(),
        }
        self._users[admin_id] = admin
        self._by_username["admin"] = admin_id
        log.info("Default admin seeded (username: admin, password: admin1234)")

    def create(self, username: str, email: str, password: str, role: str = "user") -> dict:
        if username in self._by_username:
            raise ValueError("Username already exists")
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "hashed_password": hash_password(password),
            "role": role,
            "created_at": datetime.utcnow(),
        }
        self._users[user_id] = user
        self._by_username[username] = user_id
        log.info(f"New user created: {username} ({role})")
        return user

    def get_by_username(self, username: str) -> Optional[dict]:
        uid = self._by_username.get(username)
        return self._users.get(uid) if uid else None

    def get_by_id(self, user_id: str) -> Optional[dict]:
        return self._users.get(user_id)

    def list_users(self):
        return list(self._users.values())


# Singleton
user_db = UserDB()
