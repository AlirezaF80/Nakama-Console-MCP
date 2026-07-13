from src.hints import build_list_hint
from src.pagination import MAX_BATCH_OBJECTS


def test_storage_complete_hint_suggests_batch_get():
    hint = build_list_hint(
        complete=True,
        fetched=3,
        total_count=3,
        filters={"collection": "FG", "user_id": "u1"},
    )
    assert hint is not None
    assert "nakama_get_storage_objects" in hint


def test_storage_complete_many_keys_suggests_multiple_batches():
    hint = build_list_hint(
        complete=True,
        fetched=120,
        total_count=120,
        filters={"collection": "FG", "user_id": "u1"},
    )
    assert hint is not None
    assert "120 keys returned" in hint
    batches = (120 + MAX_BATCH_OBJECTS - 1) // MAX_BATCH_OBJECTS
    assert str(batches) in hint
    assert str(MAX_BATCH_OBJECTS) in hint


def test_storage_user_id_only_warns_no_pagination():
    hint = build_list_hint(
        complete=True,
        fetched=10,
        total_count=10,
        filters={"user_id": "u1"},
    )
    assert hint is not None
    assert "no pagination" in hint
    assert "collection" in hint


def test_list_user_storage_many_objects_suggests_export():
    hint = build_list_hint(
        complete=True,
        fetched=25,
        total_count=25,
        filters={"collection": "FG", "user_id": "u1"},
        list_tool="nakama_list_user_storage",
    )
    assert hint is not None
    assert "nakama_export_account" in hint
    assert "response_mode=resource" in hint


def test_hint_includes_cursor_guidance():
    hint = build_list_hint(
        complete=False,
        fetched=100,
        total_count=500,
        filters={"collection": "FG"},
        next_cursor="abc123",
    )
    assert hint is not None
    assert "next_cursor" in hint


def test_storage_incomplete_suggests_user_id():
    hint = build_list_hint(
        complete=False,
        fetched=100,
        total_count=500,
        filters={"collection": "FG"},
    )
    assert hint is not None
    assert "user_id" in hint


def test_accounts_incomplete_suggests_filter():
    hint = build_list_hint(
        complete=False,
        fetched=100,
        total_count=200,
        filters={},
        list_kind="accounts",
    )
    assert hint is not None
    assert "filter" in hint
