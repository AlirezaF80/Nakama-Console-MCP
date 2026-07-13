from src.response_format import format_storage_object


def test_format_storage_object_omits_value():
    obj = {"collection": "c", "key": "k", "value": {"a": 1}}
    result = format_storage_object(obj, include_value=False)
    assert "value" not in result
    assert result["key"] == "k"


def test_format_storage_object_passthrough_small_value():
    obj = {"collection": "c", "key": "k", "value": {"a": 1}}
    result = format_storage_object(obj, max_value_chars=1000)
    assert result["value"] == {"a": 1}
    assert "value_preview" not in result


def test_format_storage_object_truncates_large_value():
    obj = {"collection": "c", "key": "k", "value": {"data": "x" * 5000}}
    result = format_storage_object(obj, max_value_chars=100)
    assert "value" not in result
    assert result["value_truncated"] is True
    assert len(result["value_preview"]) == 100
    assert result["value_bytes"] > 100
