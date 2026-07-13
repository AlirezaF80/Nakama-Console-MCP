import pytest

from src.validation import key_prefix_to_filter, validate_storage_key_filter


def test_validate_storage_key_filter_none():
    assert validate_storage_key_filter(None) is None
    assert validate_storage_key_filter("   ") is None


def test_validate_storage_key_filter_exact_key():
    assert validate_storage_key_filter("44") == "44"
    assert validate_storage_key_filter("  level  ") == "level"


def test_validate_storage_key_filter_prefix():
    assert validate_storage_key_filter("level%") == "level%"
    assert validate_storage_key_filter("37%") == "37%"


def test_validate_storage_key_filter_rejects_bare_percent():
    with pytest.raises(ValueError, match="Omit key"):
        validate_storage_key_filter("%")
    with pytest.raises(ValueError, match="Omit key"):
        validate_storage_key_filter("%%")


def test_validate_storage_key_filter_rejects_non_suffix_percent():
    with pytest.raises(ValueError, match="suffix %"):
        validate_storage_key_filter("%37")
    with pytest.raises(ValueError, match="suffix %"):
        validate_storage_key_filter("3%7")


def test_validate_storage_key_filter_rejects_multiple_percent():
    with pytest.raises(ValueError, match="one trailing %"):
        validate_storage_key_filter("a%b%")


def test_key_prefix_to_filter_appends_suffix():
    assert key_prefix_to_filter("level") == "level%"
    assert key_prefix_to_filter("level%") == "level%"


def test_key_prefix_to_filter_rejects_bare_percent():
    with pytest.raises(ValueError, match="Omit key"):
        key_prefix_to_filter("%")
