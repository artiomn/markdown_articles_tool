from io import StringIO
from typing import Any, List
from markdown_toolset.image_downloader import ImageDownloader


def transform_article(article_path: str, input_format_list: List[str], transformers_list: List[Any],
                      img_downloader: ImageDownloader) -> str:
    """
    Download images and fix URL's.
    """
    transformers = [tr for ifmt in input_format_list
                    for tr in transformers_list if tr is not None and tr.format == ifmt]

    with open(article_path, 'r', encoding='utf8') as article_file:
        result = StringIO(article_file.read())

    for transformer in transformers:
        lines = transformer(result, img_downloader).run()
        result = StringIO(''.join(lines))

    return result.read()
