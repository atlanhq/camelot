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

from Crypto.Util.py3compat import b, bchr
from Crypto.Util.number import bytes_to_long
from Crypto.Util.strxor import strxor
from Crypto.SelfTest.st_common import list_test_cases
from Crypto.SelfTest.loader import load_tests

from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Signature import PKCS1_PSS


def load_hash_by_name(hash_name):
    return __import__("Crypto.Hash." + hash_name, globals(), locals(), ["new"])


class PRNG(object):

    def __init__(self, stream):
        self.stream = stream
        self.idx = 0

    def __call__(self, rnd_size):
        result = self.stream[self.idx:self.idx + rnd_size]
        self.idx += rnd_size
        return result


class FIPS_PKCS1_Verify_Tests(unittest.TestCase):

    def shortDescription(self):
        return "FIPS PKCS1 Tests (Verify)"

    def verify_positive(self, hashmod, message, public_key, salt, signature):
        prng = PRNG(salt)
        hashed = hashmod.new(message)
        verifier = pss.new(public_key, salt_bytes=len(salt), rand_func=prng)
        verifier.verify(hashed, signature)

    def verify_negative(self, hashmod, message, public_key, salt, signature):
        prng = PRNG(salt)
        hashed = hashmod.new(message)
        verifier = pss.new(public_key, salt_bytes=len(salt), rand_func=prng)
        self.assertRaises(ValueError, verifier.verify, hashed, signature)

    def test_can_sign(self):
        test_public_key = RSA.generate(1024).publickey()
        verifier = pss.new(test_public_key)
        self.assertEqual(verifier.can_sign(), False)


class FIPS_PKCS1_Verify_Tests_KAT(unittest.TestCase):
    pass


test_vectors_verify = load_tests(("Crypto", "SelfTest", "Signature", "test_vectors", "PKCS1-PSS"),
                                 "SigVerPSS_186-3.rsp",
                                 "Signature Verification 186-3",
                                 { 'shaalg' : lambda x: x,
                                   'result' : lambda x: x })


for count, tv in enumerate(test_vectors_verify):
    if isinstance(tv, basestring):
        continue
    if hasattr(tv, "n"):
        modulus = tv.n
        continue
    if hasattr(tv, "p"):
        continue

    hash_module = load_hash_by_name(tv.shaalg.upper())
    hash_obj = hash_module.new(tv.msg)
    public_key = RSA.construct([bytes_to_long(x) for x in modulus, tv.e])
    if tv.saltval != b("\x00"):
        prng = PRNG(tv.saltval)
        verifier = pss.new(public_key, salt_bytes=len(tv.saltval), rand_func=prng)
    else:
        verifier = pss.new(public_key, salt_bytes=0)

    def positive_test(self, hash_obj=hash_obj, verifier=verifier, signature=tv.s):
        verifier.verify(hash_obj, signature)

    def negative_test(self, hash_obj=hash_obj, verifier=verifier, signature=tv.s):
        self.assertRaises(ValueError, verifier.verify, hash_obj, signature)

    if tv.result == 'p':
        setattr(FIPS_PKCS1_Verify_Tests_KAT, "test_positive_%d" % count, positive_test)
    else:
        setattr(FIPS_PKCS1_Verify_Tests_KAT, "test_negative_%d" % count, negative_test)


class FIPS_PKCS1_Sign_Tests(unittest.TestCase):

    def shortDescription(self):
        return "FIPS PKCS1 Tests (Sign)"

    def test_can_sign(self):
        test_private_key = RSA.generate(1024)
        signer = pss.new(test_private_key)
        self.assertEqual(signer.can_sign(), True)


class FIPS_PKCS1_Sign_Tests_KAT(unittest.TestCase):
    pass


test_vectors_sign  = load_tests(("Crypto", "SelfTest", "Signature", "test_vectors", "PKCS1-PSS"),
                                 "SigGenPSS_186-2.txt",
                                 "Signature Generation 186-2",
                                 { 'shaalg' : lambda x: x })

test_vectors_sign += load_tests(("Crypto", "SelfTest", "Signature", "test_vectors", "PKCS1-PSS"),
                                 "SigGenPSS_186-3.txt",
                                 "Signature Generation 186-3",
                                 { 'shaalg' : lambda x: x })

for count, tv in enumerate(test_vectors_sign):
    if isinstance(tv, basestring):
        continue
    if hasattr(tv, "n"):
        modulus = tv.n
        continue
    if hasattr(tv, "e"):
        private_key = RSA.construct([bytes_to_long(x) for x in modulus, tv.e, tv.d])
        continue

    hash_module = load_hash_by_name(tv.shaalg.upper())
    hash_obj = hash_module.new(tv.msg)
    if tv.saltval != b("\x00"):
        prng = PRNG(tv.saltval)
        signer = pss.new(private_key, salt_bytes=len(tv.saltval), rand_func=prng)
    else:
        signer = pss.new(private_key, salt_bytes=0)

    def new_test(self, hash_obj=hash_obj, signer=signer, result=tv.s):
        signature = signer.sign(hash_obj)
        self.assertEqual(signature, result)

    setattr(FIPS_PKCS1_Sign_Tests_KAT, "test_%d" % count, new_test)


class PKCS1_Legacy_Module_Tests(unittest.TestCase):
    """Verify that the legacy module Crypto.Signature.PKCS1_PSS
    behaves as expected. The only difference is that the verify()
    method returns True/False and does not raise exceptions."""

    def shortDescription(self):
        return "Test legacy Crypto.Signature.PKCS1_PSS"

    def runTest(self):
        key = RSA.generate(1024)
        hashed = SHA1.new(b("Test"))
        good_signature = PKCS1_PSS.new(key).sign(hashed)
        verifier = PKCS1_PSS.new(key.publickey())

        self.assertEqual(verifier.verify(hashed, good_signature), True)

        # Flip a few bits in the signature
        bad_signature = strxor(good_signature, bchr(1) * len(good_signature))
        self.assertEqual(verifier.verify(hashed, bad_signature), False)


class PKCS1_All_Hashes_Tests(unittest.TestCase):

    def shortDescription(self):
        return "Test PKCS#1 PSS signature in combination with all hashes"

    def runTest(self):

        key = RSA.generate(1280)
        signer = pss.new(key)
        hash_names = ("MD2", "MD4", "MD5", "RIPEMD160", "SHA1",
                      "SHA224", "SHA256", "SHA384", "SHA512",
                      "SHA3_224", "SHA3_256", "SHA3_384", "SHA3_512")

        for name in hash_names:
            hashed = load_hash_by_name(name).new(b("Test"))
            signer.sign(hashed)

        from Crypto.Hash import BLAKE2b, BLAKE2s
        for hash_size in (20, 32, 48, 64):
            hashed_b = BLAKE2b.new(digest_bytes=hash_size, data=b("Test"))
            signer.sign(hashed_b)
        for hash_size in (16, 20, 28, 32):
            hashed_s = BLAKE2s.new(digest_bytes=hash_size, data=b("Test"))
            signer.sign(hashed_s)


def get_tests(config={}):
    tests = []
    tests += list_test_cases(FIPS_PKCS1_Verify_Tests)
    tests += list_test_cases(FIPS_PKCS1_Sign_Tests)
    tests += list_test_cases(PKCS1_Legacy_Module_Tests)
    tests += list_test_cases(PKCS1_All_Hashes_Tests)

    if config.get('slow_tests'):
        tests += list_test_cases(FIPS_PKCS1_Verify_Tests_KAT)
        tests += list_test_cases(FIPS_PKCS1_Sign_Tests_KAT)

    return tests

if __name__ == '__main__':
    suite = lambda: unittest.TestSuite(get_tests())
    unittest.main(defaultTest='suite')
