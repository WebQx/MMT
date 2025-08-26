from postprocess import normalize_text, split_sentences


def test_normalize_text():
    assert normalize_text(" Hello   world \n") == "Hello world"


def test_split_sentences():
    s = split_sentences("Hello world. How are you? Fine!")
    assert s == ["Hello world.", "How are you?", "Fine!"]
