![Python application](https://github.com/artiomn/markdown_images_downloader/workflows/Python%20application/badge.svg)

# Markdown articles image links fixer

Version 0.0.2.

Simple script to download images and replace image links in markdown documents.
I.e. you have Markdown document with HTTP links.
This script will find all links to images, download images and fix links in the document.


## Usage

Syntax:

```
sage: images_extractor.py [-h] [-s SKIP_LIST] [-d IMAGES_DIRNAME]
                           [-p IMAGES_PUBLICPATH] [-a]
                           [-t DOWNLOADING_TIMEOUT] [-D] [--version]
                           article_file_path

Simple script to download images and replace image links in markdown
documents.

positional arguments:
  article_file_path     path to the article file in the Markdown format

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
  --version             return version number
```

Example:

```
./images_extractor.py nc-1-zfs/article.md
```

Example 2:

```
./images_extractor.py not-nas/sov/article.md -s "http://www.ossec.net/_images/ossec-arch.jpg" -a
```

Example 3 (run on a folder):

```
find content/ -name "*.md" | xargs -n1 ./images_extractor.py
```

## Warning

This tool will download only images, used Markdown syntax to link.
Images, linked with HTML "\<img\>" tag will not be downloaded!


