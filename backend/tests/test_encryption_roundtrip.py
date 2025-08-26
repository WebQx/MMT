import pytest
from persistence import store_transcript, get_transcript, reload_encryption_keys

def test_encryption_roundtrip(encryption_env):
    # encryption_env fixture sets up key material and reloads
    kid, key_b64 = encryption_env
    assert kid == 'k1'
    assert len(key_b64) > 0

    # Insert transcript (encryption should engage)
    tid = store_transcript('file.wav', 'hello world', 'summary text', {'k':'v'}, 'api')
    assert tid > 0
    rec = get_transcript(tid)
    assert rec['text'] == 'hello world'
    assert rec['summary'] == 'summary text'
    assert isinstance(rec['enrichment'], dict)
    assert rec['enrichment']['k'] == 'v'
