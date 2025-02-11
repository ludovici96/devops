import pytest
import datetime
import hashlib
from app import app
from database import get_db_connection, list_users, verify, add_user, delete_user_from_db, write_note_into_db, read_note_from_db, delete_note_from_db, setup_tables
from bs4 import BeautifulSoup

pytest_plugins = ["pytest_ordering"]

@pytest.fixture(scope='session', autouse=True)
def setup_db():
    setup_tables()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_user():
    test_id = "TEST_USER"
    test_pw = "test_password"
    add_user(test_id, test_pw)
    yield test_id, test_pw
    delete_user_from_db(test_id)

@pytest.mark.order(1)
def test_root(client):
    response = client.get('/')
    assert response.status_code == 200

@pytest.mark.order(2)
def test_public(client):
    response = client.get('/public/')
    assert response.status_code == 200

@pytest.mark.order(3)
def test_admin_unauthorized(client):
    response = client.get('/admin/')
    assert response.status_code == 401

@pytest.mark.order(4)
def test_login_logout(client, test_user):
    test_id, test_pw = test_user

    response = client.post('/login', data=dict(id=test_id, pw=test_pw), follow_redirects=True)
    print(response.data)  # Add this line to print the response data
    soup = BeautifulSoup(response.data, 'html.parser')
    h4_text = soup.find('h4').text.strip()
    assert h4_text == 'You can take notes here. Only yourself can access them. They will be removed when your account is removed.'

    response = client.get('/logout', follow_redirects=True)
    print(response.data)
    assert b"Welcome" in response.data

@pytest.mark.order(5)
def test_note_operations(client, test_user):
    test_id, test_pw = test_user
    test_note = "This is a test note."

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
