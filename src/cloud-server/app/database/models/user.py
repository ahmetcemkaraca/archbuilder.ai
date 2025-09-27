# TR: User model is now in auth_models.py for better organization
# Import the enhanced User model from auth_models to avoid duplication
from app.database.models.auth_models import User

# TR: All user-related functionality is now centralized in auth_models.py
# This file serves as a compatibility layer for existing imports

__all__ = ["User"]
