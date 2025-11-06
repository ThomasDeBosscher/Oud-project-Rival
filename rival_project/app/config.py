"""Application configuration.

Replaced dynamic environment-driven configuration with the static values
requested by the user (copied from friend's code). WARNING: Hard-coding
secrets and database credentials is insecure; prefer environment variables
in production. This is provided exactly as asked.
"""


class Config:
    SECRET_KEY = 'tamat312025.'
    # Using psycopg3 driver explicitly for consistency.
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg://postgres:tamat312025.@db.wghuuwjgvqzcdtuzzwyl.supabase.co:5432/postgres?sslmode=require'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 5,
        'max_overflow': 5,
    }
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'