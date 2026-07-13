from src.hints import build_list_hint


def test_storage_complete_hint_suggests_batch_get():
    hint = build_list_hint(
        complete=True,
        fetched=3,
        total_count=3,
        filters={"collection": "FG", "user_id": "u1"},
    )
    assert hint is not None
    assert "nakama_get_storage_objects" in hint


def test_storage_incomplete_suggests_user_id():
    hint = build_list_hint(
        complete=False,
        fetched=100,
        total_count=500,
        filters={"collection": "FG"},
    )
    assert hint is not None
    assert "user_id" in hint


def test_storage_incomplete_suggests_key_prefix():
    hint = build_list_hint(
        complete=False,
        fetched=100,
        total_count=500,
        filters={"collection": "FG", "user_id": "u1"},
    )
    assert hint is not None
    assert "key_prefix" in hint or "key" in hint


def test_storage_incomplete_last_resort_max_objects():
    hint = build_list_hint(
        complete=False,
        fetched=100,
        total_count=500,
        filters={"collection": "FG", "user_id": "u1", "key": "x%"},
    )
    assert hint is not None
    assert "max_objects" in hint


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
