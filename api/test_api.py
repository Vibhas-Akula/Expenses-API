import pytest
import requests
from flask import Flask
from app import app, init_db, insert_sample_data

# Test setup
@pytest.fixture(scope='module')
def test_client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
            insert_sample_data()
        yield client

def test_add_expense(test_client):
    # Test adding an expense
    response = test_client.post('/add_expense', json={
        'description': 'Lunch',
        'amount': 100.0,
        'paid_by': 1,
        'group_id': 1
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Expense added successfully'

def test_get_group(test_client):
    # Test fetching group details
    response = test_client.get('/get_group/1')
    assert response.status_code == 200
    data = response.get_json()
    assert 'group' in data
    assert 'users' in data
    assert 'expenses' in data

def test_get_balance(test_client):
    # Test getting balance for group
    response = test_client.get('/get_balance/1')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert '1' in data  # Check for user ID in the balance as a string

def test_invalid_expense(test_client):
    # Test adding an invalid expense
    response = test_client.post('/add_expense', json={
        'description': '',
        'amount': -100.0,
        'paid_by': 1,
        'group_id': 1
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_user_not_found(test_client):
    # Test adding an expense with a non-existent user
    response = test_client.post('/add_expense', json={
        'description': 'Dinner',
        'amount': 150.0,
        'paid_by': 999,  # Invalid user ID
        'group_id': 1
    })
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data