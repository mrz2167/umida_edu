import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_owner_id():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE role = 'owner' LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_admin_ids():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE role = 'admin'")
    admin_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return admin_ids

OWNER_ID = get_owner_id()
ADMIN_IDS = get_admin_ids()