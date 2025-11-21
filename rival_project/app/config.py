"""Application configuration.

Replaced dynamic environment-driven configuration with the static values
requested by the user (copied from friend's code). WARNING: Hard-coding
secrets and database credentials is insecure; prefer environment variables
in production. This is provided exactly as asked.
"""


import os


class Config:
    SECRET_KEY = 'tamat312025.'
    # Using psycopg3 driver explicitly for consistency.
    # Allow overriding via env (DATABASE_URL or SUPABASE_DB_URL) for local dev/offline.
    SQLALCHEMY_DATABASE_URI = (
        os.getenv('DATABASE_URL')
        or os.getenv('SUPABASE_DB_URL')
        or 'postgresql+psycopg://postgres:tamat312025.@db.wghuuwjgvqzcdtuzzwyl.supabase.co:5432/postgres?sslmode=require'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Engine options differ between drivers; avoid passing pool_size/max_overflow to SQLite.
    if str(SQLALCHEMY_DATABASE_URI).startswith('sqlite:'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 5,
            'max_overflow': 5,
        }
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'