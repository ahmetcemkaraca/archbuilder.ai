# User model is now in auth_models.py for better organization
# Import the enhanced User model from auth_models
from app.database.models.auth_models import User

__all__ = ["User"]
