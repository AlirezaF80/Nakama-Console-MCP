import pytest
from pydantic import ValidationError

from src.tools.registry import TOOL_MAP, TOOL_SPECS


def test_registry_has_unique_tool_names():
    names = [spec.name for spec in TOOL_SPECS]
    assert len(names) == len(set(names))
    assert len(TOOL_SPECS) == 12


def test_zero_arg_tools_have_empty_input_schema():
    for name in ("nakama_status", "nakama_list_collections"):
        schema = TOOL_MAP[name].input_schema()
        assert schema["type"] == "object"
        assert schema["properties"] == {}
        assert schema["additionalProperties"] is False


def test_args_tools_derive_input_schema_from_models():
    schema = TOOL_MAP["nakama_get_account"].input_schema()
    assert "id" in schema["properties"]
    assert schema["properties"]["id"]["type"] == "string"


def test_list_storage_keys_requires_collection_in_schema():
    schema = TOOL_MAP["nakama_list_storage_keys"].input_schema()
    assert "collection" in schema["required"]
