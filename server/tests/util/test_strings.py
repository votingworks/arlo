from ...util.string import format_count


def test_format_count():
    assert format_count(0, "item", "items") == "0 items"
    assert format_count(1, "item", "items") == "1 item"
    assert format_count(2, "item", "items") == "2 items"
    assert format_count(3, "item", "items") == "3 items"
    assert format_count(100, "item", "items") == "100 items"
    assert format_count(1_000, "item", "items") == "1,000 items"
    assert format_count(10_000, "item", "items") == "10,000 items"
    assert format_count(1_000_000, "item", "items") == "1,000,000 items"
    assert format_count(10_000_000, "item", "items") == "10,000,000 items"
