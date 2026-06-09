"""
config.py
---------
Application configuration loaded from environment variables.
Uses python-dotenv to load .env file values.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Flask application configuration class."""

    # MongoDB Atlas connection string
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/quiz_db")

    # Flask secret key for session management
    SECRET_KEY = os.getenv("SECRET_KEY", "quiz_secret_fallback")

    # Database name extracted from URI or default
    DB_NAME = "quiz_db"

    # Quiz timing constants (in seconds)
    QUESTION_INTRO_DURATION = 5   # Duration to show question without options
    ANSWER_DURATION = 10          # Duration for participants to answer
    REVEAL_DURATION = 4           # Duration to show correct answer

    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
