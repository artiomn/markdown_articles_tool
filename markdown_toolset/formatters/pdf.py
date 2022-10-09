"""
PDF formatter.
"""
from pathlib import Path

from markdown import markdown
import weasyprint


class PDFFormatter:
    """
    Writes lines, into the PDF.
    """

    format = 'pdf'

    @staticmethod
    def _fetcher(url):
        return weasyprint.default_url_fetcher(url, timeout=1)

    @staticmethod
    def write(lines, **kwags):
        article_base_path = article_out_path.parent if (article_out_path := kwags.get('article_out_path'))\
                                                       is not None else Path.cwd()

        return weasyprint.HTML(string=markdown(lines, output_format='html'),
                               base_url=article_base_path.as_posix(),
                               url_fetcher=PDFFormatter._fetcher).write_pdf()

        # with BytesIO() as result:
        #     pisa.pisaDocument(markdown(''.join(lines), output_format='html'), dest=result,
        #                       encoding='utf8',
        #                       link_callback=PDFFormatter._link_callback)
        #     result.seek(0)
        #     data = result.read()
        #
        # return data

        # pdfkit.from_string(markdown(''.join(lines), output_format='html'), 'fuck.pdf')
