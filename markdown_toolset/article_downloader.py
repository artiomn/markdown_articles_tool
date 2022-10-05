import logging
from pathlib import Path
from time import strftime

from .www_tools import is_url, download_from_url, get_filename_from_url, get_base_url


class ArticleDownloader:
    """
    Download article and return download path.
    """

    def __init__(self, article_url, output_path, article_formatter, downloading_timeout, remove_source: bool = False):
        self._article_file_path_or_url = article_url
        self._output_path = output_path
        self._article_formatter = article_formatter
        self._downloading_timeout = downloading_timeout
        self._remove_source = remove_source
        # TODO: Merge `article_path` and `article_out_path`.
        self._article_path = None
        self._article_out_path = None

    def get_article(self):
        self._article_path, article_base_url = self._get_article()
        self._article_out_path = self._get_article_out_path(
            article_path=self._article_path,
            output_path=Path(self._output_path) if self._output_path is not None else None,
            file_format=self._article_formatter.format
        )

        return self._article_path, article_base_url, self._article_out_path

    def _get_article(self):
        article_link = self._article_file_path_or_url

        if is_url(article_link):
            timeout = self._downloading_timeout
            if timeout < 0:
                timeout = None
            response = download_from_url(article_link, timeout=timeout)
            article_path = Path(get_filename_from_url(response))

            if article_path is None:
                article_path = Path(article_link).name

            article_base_url = get_base_url(response)

            with open(article_path, 'wb') as article_file:
                article_file.write(response.content)
                article_file.close()
        else:
            article_path = Path(article_link).expanduser()
            article_base_url = str('/'.join(article_path.parts[:-1]))

        return article_path, article_base_url

    def _need_to_change_name(self, article_path, article_out_path) -> bool:
        return (article_path == article_out_path or article_out_path.exists()) and not self._remove_source

    @staticmethod
    def _make_new_filename(output_path, article_file_name, file_format):
        return output_path / f'{article_file_name}_{strftime("%Y%m%d_%H%M%S")}.{file_format}'

    def _get_article_out_path(self, article_path: Path, output_path: Path, file_format: str) -> Path:
        article_file_name = article_path.stem

        if output_path.is_dir():
            article_out_path = output_path / f'{article_file_name}.{file_format}'
            if self._need_to_change_name(article_path, article_out_path):
                article_out_path = self._make_new_filename(output_path, article_file_name, file_format)
        elif output_path.is_file() or not output_path.exists():
            article_out_path = output_path
            if self._need_to_change_name(article_path, article_out_path):
                article_out_path = self._make_new_filename(output_path.parent, article_file_name, file_format)
        else:
            raise FileNotFoundError(f'Output path "{output_path}" is incorrect!')

        return article_out_path

    def __del__(self):
        """
        Oops...
        """

        if self._article_path is None or self._article_out_path is None:
            return

        if self._remove_source and self._article_path != self._article_out_path:
            logging.info('Removing source file "%s"...', self._article_path)
            Path(self._article_path).unlink()
