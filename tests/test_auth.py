from unittest.mock import patch

from workboard_cli.auth import check_auth


@patch("workboard_cli.auth.msal.PublicClientApplication")
@patch("workboard_cli.auth._load_msal_cache", return_value={})
@patch("workboard_cli.auth.load_config", return_value={"tenant_id": "t", "client_id": "c"})
def test_check_auth_not_authenticated(mock_config, mock_cache, mock_msal_app):
    mock_msal_app.return_value.get_accounts.return_value = []
    assert check_auth() is False


@patch("workboard_cli.auth.TOKEN_CACHE", {"token": "abc"})
def test_check_auth_authenticated_in_memory():
    assert check_auth() is True


@patch("workboard_cli.auth.msal.PublicClientApplication")
@patch("workboard_cli.auth._load_msal_cache", return_value={})
@patch("workboard_cli.auth.load_config", return_value={"tenant_id": "t", "client_id": "c"})
def test_check_auth_authenticated_via_silent(mock_config, mock_cache, mock_msal_app):
    mock_msal_app.return_value.get_accounts.return_value = ["an-account"]
    mock_msal_app.return_value.acquire_token_silent.return_value = {"access_token": "abc"}
    assert check_auth() is True
