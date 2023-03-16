from pathlib import Path

from markdown_toolset.string_tools import is_binary_same


class TestBinaryComparator:
    def setup_method(self):
        basedir = Path(__file__).parent
        self._f1 = open(basedir / 'data/img/lenna1.jpg', 'rb')
        self._f2 = open(basedir / 'data/img/lenna2.jpg', 'rb')

    def __del__(self):
        self._f2.close()
        self._f1.close()

    def test_binary_files_compare(self):
        assert is_binary_same(self._f1, self._f2) == True  # noqa
