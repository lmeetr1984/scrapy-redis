#coding=utf8
import six


def bytes_to_str(s, encoding='utf-8'):
    """Returns a str if a bytes object is given."""

    # 如果是python3的话，把byte => unicode
    if six.PY3 and isinstance(s, bytes):
        return s.decode(encoding)
    return s
