"""
HTML formatter.
"""

from markdown import markdown
from pygments.formatters import HtmlFormatter
from markdown.extensions.codehilite import CodeHiliteExtension


class CustomHtmlFormatter(HtmlFormatter):
    def __init__(self, lang_str='', **options):
        super().__init__(**options)
        # lang_str has the value {lang_prefix}{lang}
        # specified by the CodeHilite's options
        self.lang_str = lang_str

    def _wrap_code(self, source):
        yield 0, f'<code class="{self.lang_str}">'
        yield from source
        yield 0, '</code>'


class HTMLFormatter:
    """
    Convert lines in the HTML.
    """

    format = 'html'

    @staticmethod
    def write(lines, **kwargs):
        del kwargs

        html_formatter = CustomHtmlFormatter()
        md = markdown(lines, output_format='html', extensions=['fenced_code',
                                                               CodeHiliteExtension(pygments_formatter=html_formatter),
                                                               'tables', 'toc'])
        return f'<html>\n<head><style>\n{html_formatter.get_style_defs()}\n</style></head>\n' \
               f'<body>\n{md}\n</body>\n</html>'.encode()
