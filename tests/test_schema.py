from workboard_cli.schema import _get_column_type


def test_column_type_text():
    col = {"text": {"textType": "plain"}}
    assert _get_column_type(col) == "text"


def test_column_type_number():
    col = {"number": {}}
    assert _get_column_type(col) == "number"


def test_column_type_choice():
    col = {"choice": {}}
    assert _get_column_type(col) == "choice"


def test_column_type_person():
    col = {"personOrGroup": {}}
    assert _get_column_type(col) == "personOrGroup"


def test_column_type_lookup():
    col = {"lookup": {"listId": "abc"}}
    assert _get_column_type(col) == "lookup"
