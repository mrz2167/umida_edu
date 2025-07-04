import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()
from urllib.parse import urlparse

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    parsed = urlparse(DATABASE_URL)
    psycopg2.connect(
        dbname=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port
    )



def get_owner_id():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE role = 'owner' LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_admin_ids():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE role = 'admin'")
    admin_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return admin_ids

def get_admin_ester_id():
    """Получает ID администратора Esther (специальный админ)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE role = 'Ester' LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

OWNER_ID = get_owner_id()
ADMIN_ESTER = get_admin_ester_id()
ADMIN_IDS = get_admin_ids()
ALL_ADMINS = list(set([OWNER_ID, ADMIN_ESTER] + ADMIN_IDS))
ADMIN_GROUP_ID = -1002753246363
ADMINISTRATION = {
    "OWNER_ID": OWNER_ID,
    "ADMIN_ESTER": ADMIN_ESTER
}

print(f"Owner ID: {OWNER_ID}")
# print(f"Admin Esther ID: {ADMIN_ESTER}")
# print(f"Admin IDs: {ADMIN_IDS}")
# print("ADMINISTRATION:", ADMINISTRATION)
