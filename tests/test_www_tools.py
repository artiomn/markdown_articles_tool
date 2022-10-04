from markdown_toolset.www_tools import remove_protocol_prefix, is_url


class TestProtocolPrefixesFunctions:
    def test_prefix_remover(self):
        assert remove_protocol_prefix('http://test.url') == 'test.url'
        assert remove_protocol_prefix('https://test.url') == 'test.url'
        assert remove_protocol_prefix('HTTPS://test.url') == 'test.url'
        assert remove_protocol_prefix('Ftp://test.url') == 'test.url'
        assert remove_protocol_prefix('FtpS://test.url') == 'test.url'
        assert remove_protocol_prefix('file://test.url') == 'test.url'
        assert remove_protocol_prefix('FtpS://http://test.url') == 'http://test.url'
        assert remove_protocol_prefix('ftps://ftps://test.url') == 'ftps://test.url'

    def test_url_checker(self):
        assert is_url('http://test') == True  # noqa
        assert is_url('ftp://test') == True  # noqa
        assert is_url('Https://test') == True  # noqa
        assert is_url('FTPS://test') == True  # noqa
        assert is_url('file://test') == False  # noqa
