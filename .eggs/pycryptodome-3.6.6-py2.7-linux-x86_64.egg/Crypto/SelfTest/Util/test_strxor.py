#
#  SelfTest/Util/test_strxor.py: Self-test for XORing
#
# ===================================================================
#
# Copyright (c) 2014, Legrandin <helderijs@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ===================================================================

import unittest
from binascii import unhexlify, hexlify

from Crypto.Util.py3compat import _memoryview
from Crypto.SelfTest.st_common import list_test_cases
from Crypto.Util.strxor import strxor, strxor_c


class StrxorTests(unittest.TestCase):

    def test1(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        term2 = unhexlify(b"383d4ba020573314395b")
        result = unhexlify(b"c70ed123c59a7fcb6f12")
        self.assertEqual(strxor(term1, term2), result)
        self.assertEqual(strxor(term2, term1), result)

    def test2(self):
        es = b""
        self.assertEqual(strxor(es, es), es)

    def test3(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        all_zeros = b"\x00" * len(term1)
        self.assertEqual(strxor(term1, term1), all_zeros)

    def test_wrong_length(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        term2 = unhexlify(b"ff339a83e5cd4cdf564990")
        self.assertRaises(ValueError, strxor, term1, term2)

    def test_bytearray(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        term1_ba = bytearray(term1)
        term2 = unhexlify(b"383d4ba020573314395b")
        result = unhexlify(b"c70ed123c59a7fcb6f12")

        self.assertEqual(strxor(term1_ba, term2), result)
    
    def test_memoryview(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        term1_mv = memoryview(term1)
        term2 = unhexlify(b"383d4ba020573314395b")
        result = unhexlify(b"c70ed123c59a7fcb6f12")

        self.assertEqual(strxor(term1_mv, term2), result)

    import types
    if _memoryview is types.NoneType:
        del test_memoryview


class Strxor_cTests(unittest.TestCase):

    def test1(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        result = unhexlify(b"be72dbc2a48c0d9e1708")
        self.assertEqual(strxor_c(term1, 65), result)

    def test2(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        self.assertEqual(strxor_c(term1, 0), term1)

    def test3(self):
        self.assertEqual(strxor_c(b"", 90), b"")

    def test_wrong_range(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        self.assertRaises(ValueError, strxor_c, term1, -1)
        self.assertRaises(ValueError, strxor_c, term1, 256)

    def test_bytearray(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        term1_ba = bytearray(term1)
        result = unhexlify(b"be72dbc2a48c0d9e1708")

        self.assertEqual(strxor_c(term1_ba, 65), result)
    
    def test_memoryview(self):
        term1 = unhexlify(b"ff339a83e5cd4cdf5649")
        term1_mv = memoryview(term1)
        result = unhexlify(b"be72dbc2a48c0d9e1708")

        self.assertEqual(strxor_c(term1_mv, 65), result)

    import types
    if _memoryview is types.NoneType:
        del test_memoryview


def get_tests(config={}):
    tests = []
    tests += list_test_cases(StrxorTests)
    tests += list_test_cases(Strxor_cTests)
    return tests


if __name__ == '__main__':
    suite = lambda: unittest.TestSuite(get_tests())
    unittest.main(defaultTest='suite')
