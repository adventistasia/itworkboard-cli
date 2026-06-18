from workboard_cli.auth import check_auth


def test_check_auth_not_authenticated():
    assert check_auth() is False
