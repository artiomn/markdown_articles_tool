from markdown_toolset.www_tools import is_url


class TestIsUrlEdgeCases:
    def test_none_is_not_a_url(self):
        assert is_url(None) is False

    def test_non_string_is_not_a_url(self):
        assert is_url(123) is False
        assert is_url(b'http://test') is False

    def test_regular_urls_still_detected(self):
        assert is_url('http://test') is True
        assert is_url('https://test') is True
        assert is_url('file://test') is False
