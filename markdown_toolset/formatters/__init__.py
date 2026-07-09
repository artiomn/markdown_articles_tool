from .simple import SimpleFormatter
from .html import HTMLFormatter
from .docx import DOCXFormatter
from .helpers import format_article, get_formatter


FORMATTERS = [SimpleFormatter, HTMLFormatter, DOCXFormatter]


try:
    from .pdf import PDFFormatter

    FORMATTERS.append(PDFFormatter)
except ModuleNotFoundError:
    pass


__all__ = ['FORMATTERS', 'get_formatter', 'format_article']
