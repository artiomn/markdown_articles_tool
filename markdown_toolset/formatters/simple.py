"""
Simple formatter.
"""


class SimpleFormatter:
    """
    Writes lines, "as is".
    """

    format = 'md'

    @staticmethod
    def write(lines, **kwargs):
        return lines.encode('utf8')
