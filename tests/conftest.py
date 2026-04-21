# tests/conftest.py
import os
import sys

import pytest
from app.app import create_app

@pytest.fixture()
def app():
    app = create_app()
    app.config["TESTING"]              = True
    app.config["SESSION_COOKIE_SECURE"] = False  # HTTPS not required in tests
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def authenticated_client(client):
    """
    Returns a test client with an active authenticated session.
    Also returns the CSRF token for use in state-changing requests.
    """
    # GET /login to initialise a session and generate a CSRF token
    client.get("/login")

    with client.session_transaction() as sess:
        token = sess.get("csrf_token", "")

    client.post("/login", data={
            "username": "admin",
            "password": "L|fP1D%327mB",
            "csrf_token": token,
        }, follow_redirects=True
    )

    # After login a new token is rotated — fetch the updated one
    with client.session_transaction() as sess:
        new_token = sess.get("csrf_token", "")

    return client, new_token