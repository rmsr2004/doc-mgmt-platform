from app.app import create_app

app = create_app()


def login(client):
    """Simulate login by setting session directly (mocking auth)."""
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'alice'
        session['is_admin'] = False


def get_csrf_token(client):
    with client.session_transaction() as session:
        return session.get("csrf_token")


def login_and_get_token(client, route="/documents"):
    """Login and retrieve valid CSRF token."""
    login(client)
    client.get(route)
    return get_csrf_token(client)


def test_get_request_bypasses_csrf():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code != 403


def test_post_without_csrf_token_returns_403():
    client = app.test_client()
    login(client)

    response = client.post(
        "/documents/1/share",
        data={"share_with_user_id": "2"},
    )

    assert response.status_code == 403


def test_post_with_wrong_csrf_token_returns_403():
    client = app.test_client()
    login(client)

    response = client.post(
        "/documents/1/share",
        data={
            "share_with_user_id": "2",
            "csrf_token": "invalid-token",
        },
    )

    assert response.status_code == 403


def test_post_with_valid_csrf_passes():
    client = app.test_client()
    csrf_token = login_and_get_token(client)

    response = client.post(
        "/documents/1/share",
        data={
            "share_with_user_id": "2",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code != 403


def test_unauthenticated_post_skips_csrf_check():
    client = app.test_client()
    response = client.post(
        "/documents/1/share",
        data={"share_with_user_id": "2"},
    )
    assert response.status_code != 403


def test_health_endpoint_exempt():
    client = app.test_client()
    response = client.post("/health")

    assert response.status_code != 403


def test_csrf_token_present_in_login_form():
    client = app.test_client()
    response = client.get("/login")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'name="csrf_token"' in html
    assert 'type="hidden"' in html


def test_csrf_token_rotates_on_login():
    client = app.test_client()
    client.get("/login")
    token_before = get_csrf_token(client)

    with client.session_transaction() as session:
        session.clear()
        session['user_id'] = 1
        session['username'] = 'alice'
        session['is_admin'] = False
    
    client.get("/documents")
    token_after = get_csrf_token(client)
    assert token_before != token_after


def test_csrf_token_rotates_on_logout():
    client = app.test_client()
    client.get("/login")
    
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'alice'
        session['is_admin'] = False
    
    client.get("/documents")
    token_before = get_csrf_token(client)

    response = client.post(
        "/logout",
        data={"csrf_token": token_before},
        follow_redirects=True,
    )

    token_after = get_csrf_token(client)
    assert response.status_code != 403
    assert token_before != token_after or token_after is None