import os
from sqlalchemy import text

from app import create_app
from app.extensions import db

# Optional: allow setting a temp URL for this check via CLI ENV
# Example:
#   DATABASE_URL=sqlite:///:memory: python scripts/db_healthcheck.py

app = create_app()

with app.app_context():
    print("Configured DB URL:", db.engine.url)
    try:
        val = db.session.execute(text("select 1")).scalar()
        print("Connectivity: OK (select 1 ->)", val)
        exit(0)
    except Exception as e:
        print("Connectivity: FAIL\n", repr(e))
        print("\nHints:")
        print("- To test locally without network, run with DATABASE_URL=sqlite:///:memory:")
        print("- If Supabase is unreachable due to IPv6, try using the IPv4 address in the URL host.")
        print("- Or set DATABASE_URL/SUPABASE_DB_URL in your environment before running the app.")
        exit(1)
