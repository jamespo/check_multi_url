#!/usr/bin/env python
# test1.py

import unittest
from check_multi_url import CheckRunner, MultiCheck


class TestCheckMulti(unittest.TestCase):

    def test_nowtime(self):
        nowtime_500less = CheckRunner.nowtime(500)
        nowtime = CheckRunner.nowtime()
        assert nowtime > 0 and nowtime > nowtime_500less


if __name__ == '__main__':
    unittest.main()
