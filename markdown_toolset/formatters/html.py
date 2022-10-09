"""
HTML formatter.
"""

from markdown import markdown


class HTMLFormatter:
    """
    Convert lines in the HTML.
    """

    format = 'html'

    @staticmethod
    def write(lines, **kwargs):
        md = markdown(lines, output_format='html')
        return f'<html>\n<head></head>\n<body>\n{md}\n</body>\n</html>'.encode()
