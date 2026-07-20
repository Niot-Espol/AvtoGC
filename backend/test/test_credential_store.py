from app.services.credential_store import CanvasCredentialStore


def test_token_is_kept_server_side_only():
    store = CanvasCredentialStore()
    connection_id = store.create(
        base_url="https://canvas.example.edu",
        token="secret-token",
        profile={"name": "Usuario"},
    )
    assert "secret-token" not in connection_id
    assert store.get(connection_id).token == "secret-token"
    store.delete(connection_id)
    assert store.get(connection_id) is None
