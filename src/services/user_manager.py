import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class UserManager:
    """
    Manages the user database stored in a local JSON file.
    Handles creation of users with unique IDs and retrieval of user data.
    """
    def __init__(self, db_path: Path):
        """
        Initializes the user manager.

        Args:
            db_path: The Path object pointing to the user JSON file.
        """
        self.db_path = db_path
        self.users = self._load_users()
        logger.info(f"UserManager initialized with database file: {self.db_path}")

    def _load_users(self) -> dict:
        """Loads users from the JSON file. Returns an empty dict if not found."""
        if not self.db_path.exists():
            return {}
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Could not read user database at {self.db_path}: {e}")
            return {}

    def _save_users(self):
        """Saves the current user dictionary back to the JSON file."""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=4)
        except IOError as e:
            logger.error(f"Could not save user database to {self.db_path}: {e}")

    def create_user(self, name: str) -> tuple[str | None, dict | None]:
        """
        Creates a new user with a unique UUID if they don't already exist.

        Args:
            name: The name of the user to create.

        Returns:
            A tuple containing the new user's ID and their data, or (None, None) if failed.
        """
        # Check if a user with this name already exists to avoid duplicates
        existing_id, _ = self.get_user_by_name(name)
        if existing_id:
            logger.warning(f"User '{name}' already exists with ID {existing_id}. Cannot create duplicate.")
            return existing_id, self.users[existing_id]

        new_id = str(uuid.uuid4())
        new_user_data = {
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.users[new_id] = new_user_data
        self._save_users()
        logger.info(f"Created new user '{name}' with ID: {new_id}")
        return new_id, new_user_data

    def get_user_by_name(self, name: str) -> tuple[str | None, dict | None]:
        """Finds a user by name and returns their ID and data."""
        for user_id, user_data in self.users.items():
            if user_data.get("name") == name:
                return user_id, user_data
        return None, None
        
    def get_user_by_id(self, user_id: str) -> dict | None:
        """Finds a user by their unique ID."""
        return self.users.get(user_id)
