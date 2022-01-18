from pathlib import Path
from typing import Any, List


def get_formatter(output_format: str, formatters_list: List[Any]):
    formatter = [f for f in formatters_list if f is not None and f.format == output_format]
    assert len(formatter) == 1
    formatter = formatter[0]

    return formatter


def format_article(article_out_path: Path, article_text: str, formatter) -> None:
    """
    Save article in the selected format.
    """

    print(f'Writing file into "{article_out_path}"...')

    with open(article_out_path, 'wb') as outfile:
        outfile.write(formatter.write(article_text))
