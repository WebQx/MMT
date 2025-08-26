from persistence import store_transcript


def test_store_transcript_sqlite_fallback():
    rec_id = store_transcript(
        filename="test.wav",
        text="hello world",
        summary="hello world",
        enrichment={"entities": []},
        source="test",
    )
    assert rec_id == 1 or rec_id > 0