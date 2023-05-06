import pytest
from app import app
from database import list_users, verify, add_user, delete_user_from_db, write_note_into_db, read_note_from_db, delete_note_from_db, setup_tables

@pytest.fixture(scope='session', autouse=True)
def setup_db():
    setup_tables()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_root(client):
    response = client.get('/')
    assert response.status_code == 200

def test_public(client):
    response = client.get('/public/')
    assert response.status_code == 200

def test_admin_unauthorized(client):
    response = client.get('/admin/')
    assert response.status_code == 401

def test_login_logout(client):
    test_id = "TEST_USER"
    test_pw = "test_password"

    add_user(test_id, test_pw)

    response = client.post('/login', data=dict(id=test_id, pw=test_pw), follow_redirects=True)
    assert b"Private Page" in response.data

    response = client.get('/logout', follow_redirects=True)
    assert b"Welcome!" in response.data

    delete_user_from_db(test_id)

def test_note_operations(client):
    test_id = "TEST_USER"
    test_pw = "test_password"
    test_note = "This is a test note."

    add_user(test_id, test_pw)

    client.post('/login', data=dict(id=test_id, pw=test_pw), follow_redirects=True)

    write_note_into_db(test_id, test_note)
    notes = read_note_from_db(test_id)
    assert len(notes) == 1
    assert notes[0][2] == test_note

    note_id = notes[0][0]
    delete_note_from_db(note_id)
    notes = read_note_from_db(test_id)
    assert len(notes) == 0

    client.get('/logout', follow_redirects=True)
    delete_user_from_db(test_id)

