import pytest
from pydantic import ValidationError

from src.models import ListStorageArgs, ListStorageKeysArgs, ListUserStorageArgs


def test_list_storage_args_rejects_bare_percent_key():
    with pytest.raises(ValueError, match="Omit key"):
        ListStorageArgs.model_validate({"collection": "FG", "key": "%"})


def test_list_storage_args_accepts_prefix_key():
    args = ListStorageArgs.model_validate({"collection": "FG", "key": "37%"})
    assert args.key == "37%"


def test_list_user_storage_args_rejects_bad_prefix():
    with pytest.raises(ValueError, match="Omit key"):
        ListUserStorageArgs.model_validate({"user_id": "u1", "key_prefix": "%"})


def test_list_user_storage_args_normalizes_key_prefix():
    args = ListUserStorageArgs.model_validate({"user_id": "u1", "key_prefix": "level"})
    assert args.key_prefix == "level%"


def test_list_storage_keys_args_requires_collection():
    with pytest.raises(ValidationError):
        ListStorageKeysArgs.model_validate({"user_id": "u1"})
