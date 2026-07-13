import pytest

from src.validation import validate_storage_list_cursor


def test_rejects_cursor_with_user_id_only():
    with pytest.raises(ValueError, match="user ID"):
        validate_storage_list_cursor(
            collection=None,
            key=None,
            user_id="u1",
            cursor="abc",
        )


def test_rejects_cursor_with_exact_key_triple():
    with pytest.raises(ValueError, match="collection, key, and user_id"):
        validate_storage_list_cursor(
            collection="FG",
            key="44",
            user_id="u1",
            cursor="abc",
        )


def test_allows_cursor_with_prefix_key():
    validate_storage_list_cursor(
        collection="FG",
        key="4%",
        user_id="u1",
        cursor="abc",
    )
