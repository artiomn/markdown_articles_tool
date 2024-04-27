import requests

from markdown_toolset.www_tools import remove_protocol_prefix, is_url, get_filename_from_url, download_from_url


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

    def test_get_filename_from_url(self):
        # Mock response.
        req = requests.Response()
        req.status_code = 200
        req.headers['content-type'] = 'image/jpg'

        req.url = 'https://image.cubox.pro/cardImg/26p25dhia8yismewd0i3zptqzluz1ydufavhzlog6yjr6b6yle.jpg?imageMogr2/quality/90/ignore-error/1'
        assert get_filename_from_url(req) == 'cardimg26p25dhia8yismewd0i3zptqzluz1ydufavhzlog6yjr6b6yle.jpg'

        req.url = 'https://image.cubox.pro/cardImg/53fjbjlzb8a72slatcat03qmae7rw44qh3rvyck9548bqg06a2.jpg?imageMogr2/quality/90/ignore-error/1'
        assert get_filename_from_url(req) == 'cardimg53fjbjlzb8a72slatcat03qmae7rw44qh3rvyck9548bqg06a2.jpg'

        url = (
            'https://cubox.pro/c/filters:no_upscale()?valid=false&imageUrl=https%3A%2F%2Fpic1.zhimg.com'
            '%2F50%2Fv2-c4b89a30d2a3fe1897cfe24388ec935e_720w.jpg%3Fsource%3D1940ef5c'
        )
        req = download_from_url(url)
        assert get_filename_from_url(req) == 'cardimgo2sqp98phc0gflafoxr829sjojo4vouo8twjaqycdtakasiqc.jpg'
