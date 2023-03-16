from .simple import SimpleFormatter
from .html import HTMLFormatter
from .helpers import format_article, get_formatter


FORMATTERS = [SimpleFormatter, HTMLFormatter]


try:
    from .pdf import PDFFormatter

    FORMATTERS.append(PDFFormatter)
except ModuleNotFoundError:
    pass


__all__ = ['FORMATTERS', 'get_formatter', 'format_article']
