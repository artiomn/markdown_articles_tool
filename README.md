![Python application](https://github.com/artiomn/markdown_images_downloader/workflows/Python%20application/badge.svg)

# Markdown articles tool 0.0.4

Version 0.0.4.

Tool can be used:

- To download markdown article with images and replace image links.  
  Find all links to images, download images and fix links in the document.
  Similar images may be deduplicated by content hash.
- Convert Markdown documents to:
  * HTML.
  * PDF.


## Usage

Syntax:

```
usage: markdown_tool.py [-h] [-s SKIP_LIST] [-d IMAGES_DIRNAME]
                        [-p IMAGES_PUBLICPATH] [-a] [-t DOWNLOADING_TIMEOUT]
                        [-D] [-R] [-o {md,html,pdf}] [--version]
                        article_file_path_or_url

Simple script to download images and replace image links in markdown
documents.

positional arguments:
  article_file_path_or_url
                        path to the article file in the Markdown format

optional arguments:
  -h, --help            show this help message and exit
  -s SKIP_LIST, --skip-list SKIP_LIST
                        skip URL's from the comma-separated list (or file with
                        a leading '@')
  -d IMAGES_DIRNAME, --images-dirname IMAGES_DIRNAME
                        Folder in which to download images
  -p IMAGES_PUBLICPATH, --images-publicpath IMAGES_PUBLICPATH
                        Public path to the folder of downloaded images
  -a, --skip-all-incorrect
                        skip all incorrect images
  -t DOWNLOADING_TIMEOUT, --downloading-timeout DOWNLOADING_TIMEOUT
                        how many seconds to wait before downloading will be
                        failed
  -D, --dedup-with-hash
                        Deduplicate images, using content hash
  -R, --remove-source   Remove or replace source file
  -o {md,html,pdf}, --output-format {md,html,pdf}
                        output format
  --version             return version number
```

Example:

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

## Warning

This tool will download only images, used Markdown syntax to link.
Images, linked with HTML "\<img\>" tag will not be downloaded!
