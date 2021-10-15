![Python application](https://github.com/artiomn/markdown_images_downloader/workflows/Python%20application/badge.svg)

# Markdown articles tool 0.0.7

Tool can be used:

- To download markdown article with images and replace image links.  
  Find all links to images, download images and fix links in the document.
  Similar images may be deduplicated by content hash.
- Support images, linked with HTML `<img>` tag.
- Convert Markdown documents to:
  * HTML.
  * PDF.
  * Or save in the plain Markdown.


## Installation

You need Python 3.7+.  
Run:

```
git clone "https://github.com/artiomn/markdown_articles_tool"
pip3 install -r markdown_articles_tool/requirements.txt
```


## Usage

Syntax:

```
usage: markdown_tool.py [-h] [-D] [-d IMAGES_DIRNAME] [-a] [-s SKIP_LIST]
                        [-i {md,html,md+html,html+md}] [-o {md,html,pdf}]
                        [-p IMAGES_PUBLIC_PATH] [-R] [-t DOWNLOADING_TIMEOUT]
                        [-O OUTPUT_PATH] [--version]
                        article_file_path_or_url

Simple script to download images and replace image links in markdown
documents.

positional arguments:
  article_file_path_or_url
                        path to the article file in the Markdown format

optional arguments:
  -h, --help            show this help message and exit
  -D, --dedup-with-hash
                        Deduplicate images, using content hash
  -d IMAGES_DIRNAME, --images-dirname IMAGES_DIRNAME
                        Folder in which to download images (possible
                        variables: $article_name, $time, $date, $dt,
                        $base_url)
  -a, --skip-all-incorrect
                        skip all incorrect images
  -s SKIP_LIST, --skip-list SKIP_LIST
                        skip URL's from the comma-separated list (or file with
                        a leading '@')
  -i {md,html,md+html,html+md}, --input-format {md,html,md+html,html+md}
                        input format
  -o {md,html,pdf}, --output-format {md,html,pdf}
                        output format
  -p IMAGES_PUBLIC_PATH, --images-public-path IMAGES_PUBLIC_PATH
                        Public path to the folder of downloaded images
                        (possible variables: $article_name, $time, $date, $dt,
                        $base_url)
  -R, --remove-source   Remove or replace source file
  -t DOWNLOADING_TIMEOUT, --downloading-timeout DOWNLOADING_TIMEOUT
                        how many seconds to wait before downloading will be
                        failed
  -O OUTPUT_PATH, --output-path OUTPUT_PATH
                        article output file name
  --version             return version number
```

Example 1:

```
./markdown_tool.py nc-1-zfs/article.md
```

Example 2:

```
./markdown_tool.py not-nas/sov/article.md -o html -s "http://www.ossec.net/_images/ossec-arch.jpg" -a
```

Example 3 (run on a folder):

```
find content/ -name "*.md" | xargs -n1 ./markdown_tool.py
```

