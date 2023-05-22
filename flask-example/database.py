import psycopg2
import psycopg2.extras
import hashlib
import datetime
import os
import uuid


# PostgreSQL Database credentials loaded from the environment variables
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')


def get_db_connection():
    _conn = psycopg2.connect(host=DATABASE_HOST, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
    return _conn

def list_users():
    _conn = get_db_connection()
    _c = _conn.cursor()

    _c.execute("SELECT id FROM users;")
    result = [x[0] for x in _c.fetchall()]

    _conn.close()
    
    return result

def verify(id, pw):
    _conn = get_db_connection()
    _c = _conn.cursor()

    _c.execute("SELECT password FROM users WHERE id = %s", (id.upper(),))
    result = _c.fetchone()[0] == hashlib.sha256(pw.encode()).hexdigest()
    
    _conn.close()

    return result

def validate_login(id, pw):
    _conn = get_db_connection()
    _c = _conn.cursor()

    _c.execute("SELECT password FROM users WHERE id = %s", (id.upper(),))
    result = _c.fetchone()

    _conn.close()

    if result is None:
        return False
    return result[0] == hashlib.sha256(pw.encode()).hexdigest()

def delete_user_from_db(id):
    _conn = get_db_connection()
    _c = _conn.cursor()
    _c.execute("DELETE FROM users WHERE id = %s", (id,))
    _conn.commit()
    _conn.close()

    # when we delete a user FROM database USERS, we also need to delete all his or her notes data FROM database NOTES
    _conn = get_db_connection()
    _c = _conn.cursor()
    _c.execute("DELETE FROM notes WHERE user = %s", (id,))
    _conn.commit()
    _conn.close()

    # when we delete a user FROM database USERS, we also need to 
    # [1] delete all his or her images FROM image pool (done in app.py)
    # [2] delete all his or her images records FROM database IMAGES
    _conn = get_db_connection()
    _c = _conn.cursor()
    _c.execute("DELETE FROM images WHERE owner = %s", (id,))
    _conn.commit()
    _conn.close()

def add_user(id, pw):
    _conn = get_db_connection()
    _c = _conn.cursor()

    _c.execute("INSERT INTO users values(%s, %s)", (id.upper(), hashlib.sha256(pw.encode()).hexdigest()))
    
    _conn.commit()
    _conn.close()

def read_note_from_db(id):
    _conn = get_db_connection()
    _c = _conn.cursor()

    command = "SELECT note_id, note_timestamp, note FROM notes WHERE user_id = %s"
    _c.execute(command, (id.upper(),))
    result = _c.fetchall()

    _conn.commit()
    _conn.close()

    return result

def match_user_id_with_note_id(note_id):
    # Given the note id, confirm if the current user is the owner of the note which is being operated.
    _conn = get_db_connection()
    _c = _conn.cursor()

    command = "SELECT user FROM notes WHERE note_id = %s" 
    _c.execute(command, (note_id,))
    result = _c.fetchone()[0]

    _conn.commit()
    _conn.close()
    return result

def write_note_into_db(id, note_to_write):
    _conn = get_db_connection()
    _c = _conn.cursor()

    current_timestamp = str(datetime.datetime.now())
    note_id = hashlib.sha1((id.upper() + current_timestamp).encode()).hexdigest()
    _c.execute("INSERT INTO notes (user_id, note_timestamp, note, note_id) VALUES (%s, %s, %s, %s)", (id.upper(), current_timestamp, note_to_write, note_id))

    _conn.commit()
    _conn.close()


def delete_note_from_db(note_id):
    _conn = get_db_connection()
    _c = _conn.cursor()

    command = "DELETE FROM notes WHERE note_id = %s" 
    _c.execute(command, (note_id,))

    _conn.commit()
    _conn.close()

def image_upload_record(uid, owner, image_name, timestamp):
    _conn = get_db_connection()
    _c = _conn.cursor()

    _c.execute("INSERT INTO images VALUES (%s, %s, %s, %s)", (str(uid), owner, image_name, timestamp))

    _conn.commit()
    _conn.close()

def list_images_for_user(owner):
    _conn = get_db_connection()
    _c = _conn.cursor()

    command = "SELECT uid, timestamp, name FROM images WHERE owner = %s"
    _c.execute(command, (owner,))
    result = _c.fetchall()

    _conn.commit()
    _conn.close()

    return result

def match_user_id_with_image_uid(image_uid):
    # Given the note id, confirm if the current user is the owner of the note which is being operated.
    _conn = get_db_connection()
    _c = _conn.cursor()

    command = "SELECT owner FROM images WHERE uid = %s" 
    _c.execute(command, (image_uid,))
    result = _c.fetchone()[0]

    _conn.commit()
    _conn.close()

    return result

def delete_image_from_db(image_uid):
    _conn = get_db_connection()
    _c = _conn.cursor()

    command = "DELETE FROM images WHERE uid = %s" 
    _c.execute(command, (image_uid,))

    _conn.commit()
    _conn.close()

def setup_tables():
    _conn = get_db_connection()
    _c = _conn.cursor()

    _c.execute("SELECT to_regclass('public.users')")
    user_table_exists = _c.fetchone()[0] is not None

    _c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id text PRIMARY KEY,
        password text
    );
    """)

    _c.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        user_id text,
        note_timestamp timestamp,
        note text,
        note_id text
    );
    """)

    _c.execute("""
    CREATE TABLE IF NOT EXISTS images (
        uid uuid PRIMARY KEY,
        owner text,
        name text,
        timestamp timestamp
    );
    """)

    _conn.commit()
    _conn.close()

    if not user_table_exists:
        add_user('admin', 'admin')
        add_user('test', '123456')


if __name__ == "__main__":
    print(list_users())