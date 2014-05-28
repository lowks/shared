from __future__ import absolute_import
import s
import time


def test_timer():
    with s.time.timer() as t:
        time.sleep(1e-6)
    assert t['seconds'] > 0
