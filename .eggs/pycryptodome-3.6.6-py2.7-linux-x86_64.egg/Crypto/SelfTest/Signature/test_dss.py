#
#  SelfTest/Signature/test_dss.py: Self-test for DSS signatures
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

import re
import json
import unittest
from binascii import hexlify
from Crypto.Util.py3compat import b, tobytes, bord, bchr, unhexlify

from Crypto.Hash import SHA1, SHA224, SHA256, SHA384, SHA512
from Crypto.Signature import DSS
from Crypto.PublicKey import DSA, ECC
from Crypto.SelfTest.st_common import list_test_cases
from Crypto.SelfTest.loader import load_tests
from Crypto.Util.number import bytes_to_long, long_to_bytes

from Crypto.Util._file_system import pycryptodome_filename
from Crypto.Util.strxor import strxor


def t2b(hexstring):
    ws = hexstring.replace(" ", "").replace("\n", "")
    return unhexlify(tobytes(ws))


def t2l(hexstring):
    ws = hexstring.replace(" ", "").replace("\n", "")
    return long(ws, 16)


def load_hash_by_name(hash_name):
    return __import__("Crypto.Hash." + hash_name, globals(), locals(), ["new"])


class TestKey(object):
    pass


class TestVector(object):
    pass


class StrRNG:

    def __init__(self, randomness):
        length = len(randomness)
        self._idx = 0
        # Fix required to get the right K (see how randint() works!)
        self._randomness = long_to_bytes(bytes_to_long(randomness) - 1, length)

    def __call__(self, n):
        out = self._randomness[self._idx:self._idx + n]
        self._idx += n
        return out


class FIPS_DSA_Tests(unittest.TestCase):

    # 1st 1024 bit key from SigGen.txt
    P = 0xa8f9cd201e5e35d892f85f80e4db2599a5676a3b1d4f190330ed3256b26d0e80a0e49a8fffaaad2a24f472d2573241d4d6d6c7480c80b4c67bb4479c15ada7ea8424d2502fa01472e760241713dab025ae1b02e1703a1435f62ddf4ee4c1b664066eb22f2e3bf28bb70a2a76e4fd5ebe2d1229681b5b06439ac9c7e9d8bde283
    Q = 0xf85f0f83ac4df7ea0cdf8f469bfeeaea14156495
    G = 0x2b3152ff6c62f14622b8f48e59f8af46883b38e79b8c74deeae9df131f8b856e3ad6c8455dab87cc0da8ac973417ce4f7878557d6cdf40b35b4a0ca3eb310c6a95d68ce284ad4e25ea28591611ee08b8444bd64b25f3f7c572410ddfb39cc728b9c936f85f419129869929cdb909a6a3a99bbe089216368171bd0ba81de4fe33
    X = 0xc53eae6d45323164c7d07af5715703744a63fc3a
    Y = 0x313fd9ebca91574e1c2eebe1517c57e0c21b0209872140c5328761bbb2450b33f1b18b409ce9ab7c4cd8fda3391e8e34868357c199e16a6b2eba06d6749def791d79e95d3a4d09b24c392ad89dbf100995ae19c01062056bb14bce005e8731efde175f95b975089bdcdaea562b32786d96f5a31aedf75364008ad4fffebb970b

    key_pub = DSA.construct((Y, G, P, Q))
    key_priv = DSA.construct((Y, G, P, Q, X))

    def shortDescription(self):
        return "FIPS DSA Tests"

    def test_loopback(self):
        hashed_msg = SHA512.new(b("test"))
        signer = DSS.new(self.key_priv, 'fips-186-3')
        signature = signer.sign(hashed_msg)

        verifier = DSS.new(self.key_pub, 'fips-186-3')
        verifier.verify(hashed_msg, signature)

    def test_negative_unapproved_hashes(self):
        """Verify that unapproved hashes are rejected"""

        from Crypto.Hash import RIPEMD160

        self.description = "Unapproved hash (RIPEMD160) test"
        hash_obj = RIPEMD160.new()
        signer = DSS.new(self.key_priv, 'fips-186-3')
        self.assertRaises(ValueError, signer.sign, hash_obj)
        self.assertRaises(ValueError, signer.verify, hash_obj, b("\x00") * 40)

    def test_negative_unknown_modes_encodings(self):
        """Verify that unknown modes/encodings are rejected"""

        self.description = "Unknown mode test"
        self.assertRaises(ValueError, DSS.new, self.key_priv, 'fips-186-0')

        self.description = "Unknown encoding test"
        self.assertRaises(ValueError, DSS.new, self.key_priv, 'fips-186-3', 'xml')

    def test_asn1_encoding(self):
        """Verify ASN.1 encoding"""

        self.description = "ASN.1 encoding test"
        hash_obj = SHA1.new()
        signer = DSS.new(self.key_priv, 'fips-186-3', 'der')
        signature = signer.sign(hash_obj)

        # Verify that output looks like a DER SEQUENCE
        self.assertEqual(bord(signature[0]), 48)
        signer.verify(hash_obj, signature)

        # Verify that ASN.1 parsing fails as expected
        signature = bchr(7) + signature[1:]
        self.assertRaises(ValueError, signer.verify, hash_obj, signature)

    def test_sign_verify(self):
        """Verify public/private method"""

        self.description = "can_sign() test"
        signer = DSS.new(self.key_priv, 'fips-186-3')
        self.failUnless(signer.can_sign())

        signer = DSS.new(self.key_pub, 'fips-186-3')
        self.failIf(signer.can_sign())

class FIPS_DSA_Tests_KAT(unittest.TestCase):
    pass

test_vectors_verify = load_tests(("Crypto", "SelfTest", "Signature", "test_vectors", "DSA"),
                                 "FIPS_186_3_SigVer.rsp",
                                 "Signature Verification 186-3",
                                 {'result' : lambda x: x})

for idx, tv in enumerate(test_vectors_verify):

    if isinstance(tv, basestring):
        res = re.match(r"\[mod = L=([0-9]+), N=([0-9]+), ([a-zA-Z0-9-]+)\]", tv)
        hash_name = res.group(3).replace("-", "")
        hash_module = load_hash_by_name(hash_name)
        continue

    if hasattr(tv, "p"):
        modulus = tv.p
        generator = tv.g
        suborder = tv.q
        continue

    hash_obj = hash_module.new(tv.msg)
    key = DSA.construct([bytes_to_long(x) for x in tv.y, generator, modulus, suborder], False)
    verifier = DSS.new(key, 'fips-186-3')

    def positive_test(self, verifier=verifier, hash_obj=hash_obj, signature=tv.r+tv.s):
        verifier.verify(hash_obj, signature)

    def negative_test(self, verifier=verifier, hash_obj=hash_obj, signature=tv.r+tv.s):
        self.assertRaises(ValueError, verifier.verify, hash_obj, signature)

    if tv.result == 'p':
        setattr(FIPS_DSA_Tests_KAT, "test_verify_positive_%d" % idx, positive_test)
    else:
        setattr(FIPS_DSA_Tests_KAT, "test_verify_negative_%d" % idx, negative_test)


test_vectors_sign = load_tests(("Crypto", "SelfTest", "Signature", "test_vectors", "DSA"),
                               "FIPS_186_3_SigGen.txt",
                               "Signature Creation 186-3",
                               {})

for idx, tv in enumerate(test_vectors_sign):

    if isinstance(tv, basestring):
        res = re.match(r"\[mod = L=([0-9]+), N=([0-9]+), ([a-zA-Z0-9-]+)\]", tv)
        hash_name = res.group(3).replace("-", "")
        hash_module = load_hash_by_name(hash_name)
        continue

    if hasattr(tv, "p"):
        modulus = tv.p
        generator = tv.g
        suborder = tv.q
        continue

    hash_obj = hash_module.new(tv.msg)
    key = DSA.construct([bytes_to_long(x) for x in tv.y, generator, modulus, suborder, tv.x], False)
    signer = DSS.new(key, 'fips-186-3', randfunc=StrRNG(tv.k))

    def new_test(self, signer=signer, hash_obj=hash_obj, signature=tv.r+tv.s):
        self.assertEqual(signer.sign(hash_obj), signature)
    setattr(FIPS_DSA_Tests_KAT, "test_sign_%d" % idx, new_test)


class FIPS_ECDSA_Tests(unittest.TestCase):

    key_priv = ECC.generate(curve="P-256")
    key_pub = key_priv.public_key()

    def shortDescription(self):
        return "FIPS ECDSA Tests"

    def test_loopback(self):
        hashed_msg = SHA512.new(b("test"))
        signer = DSS.new(self.key_priv, 'fips-186-3')
        signature = signer.sign(hashed_msg)

        verifier = DSS.new(self.key_pub, 'fips-186-3')
        verifier.verify(hashed_msg, signature)

    def test_negative_unapproved_hashes(self):
        """Verify that unapproved hashes are rejected"""

        from Crypto.Hash import SHA1

        self.description = "Unapproved hash (SHA-1) test"
        hash_obj = SHA1.new()
        signer = DSS.new(self.key_priv, 'fips-186-3')
        self.assertRaises(ValueError, signer.sign, hash_obj)
        self.assertRaises(ValueError, signer.verify, hash_obj, b("\x00") * 40)

    def test_sign_verify(self):
        """Verify public/private method"""

        self.description = "can_sign() test"
        signer = DSS.new(self.key_priv, 'fips-186-3')
        self.failUnless(signer.can_sign())

        signer = DSS.new(self.key_pub, 'fips-186-3')
        self.failIf(signer.can_sign())

    def test_negative_unknown_modes_encodings(self):
        """Verify that unknown modes/encodings are rejected"""

        self.description = "Unknown mode test"
        self.assertRaises(ValueError, DSS.new, self.key_priv, 'fips-186-0')

        self.description = "Unknown encoding test"
        self.assertRaises(ValueError, DSS.new, self.key_priv, 'fips-186-3', 'xml')

    def test_asn1_encoding(self):
        """Verify ASN.1 encoding"""

        self.description = "ASN.1 encoding test"
        hash_obj = SHA256.new()
        signer = DSS.new(self.key_priv, 'fips-186-3', 'der')
        signature = signer.sign(hash_obj)

        # Verify that output looks like a DER SEQUENCE
        self.assertEqual(bord(signature[0]), 48)
        signer.verify(hash_obj, signature)

        # Verify that ASN.1 parsing fails as expected
        signature = bchr(7) + signature[1:]
        self.assertRaises(ValueError, signer.verify, hash_obj, signature)


class FIPS_ECDSA_Tests_KAT(unittest.TestCase):
    pass


test_vectors_verify = load_tests(("Crypto", "SelfTest", "Signature", "test_vectors", "ECDSA"),
                                 "SigVer.rsp",
                                 "ECDSA Signature Verification 186-3",
                                 {'result': lambda x: x,
                                  'qx': lambda x: int(x, 16),
                                  'qy': lambda x: int(x, 16),
                                  })

for idx, tv in enumerate(test_vectors_verify):

    if isinstance(tv, basestring):
        res = re.match(r"\[P-256,(SHA-[0-9]+)\]", tv)
        assert res
        hash_name = res.group(1).replace("-", "")
        hash_module = load_hash_by_name(hash_name)
        continue

    hash_obj = hash_module.new(tv.msg)
    key = ECC.construct(curve="P-256", point_x=tv.qx, point_y=tv.qy)
    verifier = DSS.new(key, 'fips-186-3')

    def positive_test(self, verifier=verifier, hash_obj=hash_obj, signature=tv.r+tv.s):
        verifier.verify(hash_obj, signature)

    def negative_test(self, verifier=verifier, hash_obj=hash_obj, signature=tv.r+tv.s):
        self.assertRaises(ValueError, verifier.verify, hash_obj, signature)

    if tv.result.startswith('p'):
        setattr(FIPS_ECDSA_Tests_KAT, "test_verify_positive_%d" % idx, positive_test)
    else:
        setattr(FIPS_ECDSA_Tests_KAT, "test_verify_negative_%d" % idx, negative_test)


test_vectors_sign = load_tests(("Crypto", "SelfTest", "Signature", "test_vectors", "ECDSA"),
                               "SigGen.txt",
                               "ECDSA Signature Verification 186-3",
                               {'d': lambda x: int(x, 16)})

for idx, tv in enumerate(test_vectors_sign):

    if isinstance(tv, basestring):
        res = re.match(r"\[P-256,(SHA-[0-9]+)\]", tv)
        assert res
        hash_name = res.group(1).replace("-", "")
        hash_module = load_hash_by_name(hash_name)
        continue

    hash_obj = hash_module.new(tv.msg)
    key = ECC.construct(curve="P-256", d=tv.d)
    signer = DSS.new(key, 'fips-186-3', randfunc=StrRNG(tv.k))

    def new_test(self, signer=signer, hash_obj=hash_obj, signature=tv.r+tv.s):
        self.assertEqual(signer.sign(hash_obj), signature)
    setattr(FIPS_ECDSA_Tests_KAT, "test_sign_%d" % idx, new_test)


class Det_DSA_Tests(unittest.TestCase):
    """Tests from rfc6979"""

    keys = {}
    key = TestKey()

    key.p = """
            86F5CA03DCFEB225063FF830A0C769B9DD9D6153AD91D7CE27F787C43278B447
            E6533B86B18BED6E8A48B784A14C252C5BE0DBF60B86D6385BD2F12FB763ED88
            73ABFD3F5BA2E0A8C0A59082EAC056935E529DAF7C610467899C77ADEDFC846C
            881870B7B19B2B58F9BE0521A17002E3BDD6B86685EE90B3D9A1B02B782B1779"""
    key.q = "996F967F6C8E388D9E28D01E205FBA957A5698B1"
    key.g = """
            07B0F92546150B62514BB771E2A0C0CE387F03BDA6C56B505209FF25FD3C133D
            89BBCD97E904E09114D9A7DEFDEADFC9078EA544D2E401AEECC40BB9FBBF78FD
            87995A10A1C27CB7789B594BA7EFB5C4326A9FE59A070E136DB77175464ADCA4
            17BE5DCE2F40D10A46A3A3943F26AB7FD9C0398FF8C76EE0A56826A8A88F1DBD"""
    key.x = "411602CB19A6CCC34494D79D98EF1E7ED5AF25F7"
    key.y = """
            5DF5E01DED31D0297E274E1691C192FE5868FEF9E19A84776454B100CF16F653
            92195A38B90523E2542EE61871C0440CB87C322FC4B4D2EC5E1E7EC766E1BE8D
            4CE935437DC11C3C8FD426338933EBFE739CB3465F4D3668C5E473508253B1E6
            82F65CBDC4FAE93C2EA212390E54905A86E2223170B44EAA7DA5DD9FFCFB7F3B"""
    keys['DSA1024'] = key

    key = TestKey()
    key.p = """
            9DB6FB5951B66BB6FE1E140F1D2CE5502374161FD6538DF1648218642F0B5C48
            C8F7A41AADFA187324B87674FA1822B00F1ECF8136943D7C55757264E5A1A44F
            FE012E9936E00C1D3E9310B01C7D179805D3058B2A9F4BB6F9716BFE6117C6B5
            B3CC4D9BE341104AD4A80AD6C94E005F4B993E14F091EB51743BF33050C38DE2
            35567E1B34C3D6A5C0CEAA1A0F368213C3D19843D0B4B09DCB9FC72D39C8DE41
            F1BF14D4BB4563CA28371621CAD3324B6A2D392145BEBFAC748805236F5CA2FE
            92B871CD8F9C36D3292B5509CA8CAA77A2ADFC7BFD77DDA6F71125A7456FEA15
            3E433256A2261C6A06ED3693797E7995FAD5AABBCFBE3EDA2741E375404AE25B"""
    key.q = "F2C3119374CE76C9356990B465374A17F23F9ED35089BD969F61C6DDE9998C1F"
    key.g = """
            5C7FF6B06F8F143FE8288433493E4769C4D988ACE5BE25A0E24809670716C613
            D7B0CEE6932F8FAA7C44D2CB24523DA53FBE4F6EC3595892D1AA58C4328A06C4
            6A15662E7EAA703A1DECF8BBB2D05DBE2EB956C142A338661D10461C0D135472
            085057F3494309FFA73C611F78B32ADBB5740C361C9F35BE90997DB2014E2EF5
            AA61782F52ABEB8BD6432C4DD097BC5423B285DAFB60DC364E8161F4A2A35ACA
            3A10B1C4D203CC76A470A33AFDCBDD92959859ABD8B56E1725252D78EAC66E71
            BA9AE3F1DD2487199874393CD4D832186800654760E1E34C09E4D155179F9EC0
            DC4473F996BDCE6EED1CABED8B6F116F7AD9CF505DF0F998E34AB27514B0FFE7"""
    key.x = "69C7548C21D0DFEA6B9A51C9EAD4E27C33D3B3F180316E5BCAB92C933F0E4DBC"
    key.y = """
            667098C654426C78D7F8201EAC6C203EF030D43605032C2F1FA937E5237DBD94
            9F34A0A2564FE126DC8B715C5141802CE0979C8246463C40E6B6BDAA2513FA61
            1728716C2E4FD53BC95B89E69949D96512E873B9C8F8DFD499CC312882561ADE
            CB31F658E934C0C197F2C4D96B05CBAD67381E7B768891E4DA3843D24D94CDFB
            5126E9B8BF21E8358EE0E0A30EF13FD6A664C0DCE3731F7FB49A4845A4FD8254
            687972A2D382599C9BAC4E0ED7998193078913032558134976410B89D2C171D1
            23AC35FD977219597AA7D15C1A9A428E59194F75C721EBCBCFAE44696A499AFA
            74E04299F132026601638CB87AB79190D4A0986315DA8EEC6561C938996BEADF"""
    keys['DSA2048'] = key

    # This is a sequence of items:
    # message, k, r, s, hash module
    signatures = [
            (
                "sample",
                "7BDB6B0FF756E1BB5D53583EF979082F9AD5BD5B",
                "2E1A0C2562B2912CAAF89186FB0F42001585DA55",
                "29EFB6B0AFF2D7A68EB70CA313022253B9A88DF5",
                SHA1,
                'DSA1024'
            ),
            (
                "sample",
                "562097C06782D60C3037BA7BE104774344687649",
                "4BC3B686AEA70145856814A6F1BB53346F02101E",
                "410697B92295D994D21EDD2F4ADA85566F6F94C1",
                SHA224,
                'DSA1024'
            ),
            (
                "sample",
                "519BA0546D0C39202A7D34D7DFA5E760B318BCFB",
                "81F2F5850BE5BC123C43F71A3033E9384611C545",
                "4CDD914B65EB6C66A8AAAD27299BEE6B035F5E89",
                SHA256,
                'DSA1024'
            ),
            (
                "sample",
                "95897CD7BBB944AA932DBC579C1C09EB6FCFC595",
                "07F2108557EE0E3921BC1774F1CA9B410B4CE65A",
                "54DF70456C86FAC10FAB47C1949AB83F2C6F7595",
                SHA384,
                'DSA1024'
            ),
            (
                "sample",
                "09ECE7CA27D0F5A4DD4E556C9DF1D21D28104F8B",
                "16C3491F9B8C3FBBDD5E7A7B667057F0D8EE8E1B",
                "02C36A127A7B89EDBB72E4FFBC71DABC7D4FC69C",
                SHA512,
                'DSA1024'
            ),
            (
                "test",
                "5C842DF4F9E344EE09F056838B42C7A17F4A6433",
                "42AB2052FD43E123F0607F115052A67DCD9C5C77",
                "183916B0230D45B9931491D4C6B0BD2FB4AAF088",
                SHA1,
                'DSA1024'
            ),
            (
                "test",
                "4598B8EFC1A53BC8AECD58D1ABBB0C0C71E67297",
                "6868E9964E36C1689F6037F91F28D5F2C30610F2",
                "49CEC3ACDC83018C5BD2674ECAAD35B8CD22940F",
                SHA224,
                'DSA1024'
            ),
            (
                "test",
                "5A67592E8128E03A417B0484410FB72C0B630E1A",
                "22518C127299B0F6FDC9872B282B9E70D0790812",
                "6837EC18F150D55DE95B5E29BE7AF5D01E4FE160",
                SHA256,
                'DSA1024'
            ),
            (
                "test",
                "220156B761F6CA5E6C9F1B9CF9C24BE25F98CD89",
                "854CF929B58D73C3CBFDC421E8D5430CD6DB5E66",
                "91D0E0F53E22F898D158380676A871A157CDA622",
                SHA384,
                'DSA1024'
            ),
            (
                "test",
                "65D2C2EEB175E370F28C75BFCDC028D22C7DBE9C",
                "8EA47E475BA8AC6F2D821DA3BD212D11A3DEB9A0",
                "7C670C7AD72B6C050C109E1790008097125433E8",
                SHA512,
                'DSA1024'
            ),
            (
                "sample",
                "888FA6F7738A41BDC9846466ABDB8174C0338250AE50CE955CA16230F9CBD53E",
                "3A1B2DBD7489D6ED7E608FD036C83AF396E290DBD602408E8677DAABD6E7445A",
                "D26FCBA19FA3E3058FFC02CA1596CDBB6E0D20CB37B06054F7E36DED0CDBBCCF",
                SHA1,
                'DSA2048'
            ),
            (
                "sample",
                "BC372967702082E1AA4FCE892209F71AE4AD25A6DFD869334E6F153BD0C4D806",
                "DC9F4DEADA8D8FF588E98FED0AB690FFCE858DC8C79376450EB6B76C24537E2C",
                "A65A9C3BC7BABE286B195D5DA68616DA8D47FA0097F36DD19F517327DC848CEC",
                SHA224,
                'DSA2048'
            ),
            (
                "sample",
                "8926A27C40484216F052F4427CFD5647338B7B3939BC6573AF4333569D597C52",
                "EACE8BDBBE353C432A795D9EC556C6D021F7A03F42C36E9BC87E4AC7932CC809",
                "7081E175455F9247B812B74583E9E94F9EA79BD640DC962533B0680793A38D53",
                SHA256,
                'DSA2048'
            ),
            (
                "sample",
                "C345D5AB3DA0A5BCB7EC8F8FB7A7E96069E03B206371EF7D83E39068EC564920",
                "B2DA945E91858834FD9BF616EBAC151EDBC4B45D27D0DD4A7F6A22739F45C00B",
                "19048B63D9FD6BCA1D9BAE3664E1BCB97F7276C306130969F63F38FA8319021B",
                SHA384,
                'DSA2048'
            ),
            (
                "sample",
                "5A12994431785485B3F5F067221517791B85A597B7A9436995C89ED0374668FC",
                "2016ED092DC5FB669B8EFB3D1F31A91EECB199879BE0CF78F02BA062CB4C942E",
                "D0C76F84B5F091E141572A639A4FB8C230807EEA7D55C8A154A224400AFF2351",
                SHA512,
                'DSA2048'
            ),
            (
                "test",
                "6EEA486F9D41A037B2C640BC5645694FF8FF4B98D066A25F76BE641CCB24BA4F",
                "C18270A93CFC6063F57A4DFA86024F700D980E4CF4E2CB65A504397273D98EA0",
                "414F22E5F31A8B6D33295C7539C1C1BA3A6160D7D68D50AC0D3A5BEAC2884FAA",
                SHA1,
                'DSA2048'
            ),
            (
                "test",
                "06BD4C05ED74719106223BE33F2D95DA6B3B541DAD7BFBD7AC508213B6DA6670",
                "272ABA31572F6CC55E30BF616B7A265312018DD325BE031BE0CC82AA17870EA3",
                "E9CC286A52CCE201586722D36D1E917EB96A4EBDB47932F9576AC645B3A60806",
                SHA224,
                'DSA2048'
            ),
            (
                "test",
                "1D6CE6DDA1C5D37307839CD03AB0A5CBB18E60D800937D67DFB4479AAC8DEAD7",
                "8190012A1969F9957D56FCCAAD223186F423398D58EF5B3CEFD5A4146A4476F0",
                "7452A53F7075D417B4B013B278D1BB8BBD21863F5E7B1CEE679CF2188E1AB19E",
                SHA256,
                'DSA2048'
            ),
            (
                "test",
                "206E61F73DBE1B2DC8BE736B22B079E9DACD974DB00EEBBC5B64CAD39CF9F91C",
                "239E66DDBE8F8C230A3D071D601B6FFBDFB5901F94D444C6AF56F732BEB954BE",
                "6BD737513D5E72FE85D1C750E0F73921FE299B945AAD1C802F15C26A43D34961",
                SHA384,
                'DSA2048'
            ),
            (
                "test",
                "AFF1651E4CD6036D57AA8B2A05CCF1A9D5A40166340ECBBDC55BE10B568AA0AA",
                "89EC4BB1400ECCFF8E7D9AA515CD1DE7803F2DAFF09693EE7FD1353E90A68307",
                "C9F0BDABCC0D880BB137A994CC7F3980CE91CC10FAF529FC46565B15CEA854E1",
                SHA512,
                'DSA2048'
            )
        ]

    def setUp(self):
        # Convert DSA key components from hex strings to integers
        new_keys = {}
        for tag, test_key in self.keys.items():
            new_test_key = TestKey()
            new_test_key.p = t2l(test_key.p)
            new_test_key.q = t2l(test_key.q)
            new_test_key.g = t2l(test_key.g)
            new_test_key.x = t2l(test_key.x)
            new_test_key.y = t2l(test_key.y)
            new_keys[tag] = new_test_key
        self.keys = new_keys

        # Convert signature encoding
        new_signatures = []
        for tv in self.signatures:
            new_tv = TestVector()
            new_tv.message = b(tv[0])      # message
            new_tv.nonce = t2l(tv[1])
            new_tv.result = t2b(tv[2]) + t2b(tv[3])
            new_tv.module = tv[4]
            new_tv.test_key = self.keys[tv[5]]
            new_signatures.append(new_tv)
        self.signatures = new_signatures

    def test1(self):
        q = 0x4000000000000000000020108A2E0CC0D99F8A5EFL
        x = 0x09A4D6792295A7F730FC3F2B49CBC0F62E862272FL
        p = 2 * q + 1
        y = pow(2, x, p)
        key = DSA.construct([pow(y, 2, p), 2L, p, q, x], False)
        signer = DSS.new(key, 'deterministic-rfc6979')

        # Test _int2octets
        self.assertEqual(hexlify(signer._int2octets(x)),
            b("009a4d6792295a7f730fc3f2b49cbc0f"
              "62e862272f"))

        # Test _bits2octets
        h1 = SHA256.new(b("sample")).digest()
        self.assertEqual(hexlify(signer._bits2octets(h1)),
            b("01795edf0d54db760f156d0dac04c032"
              "2b3a204224"))

    def test2(self):

        for sig in self.signatures:
            tk = sig.test_key
            key = DSA.construct([tk.y, tk.g, tk.p, tk.q, tk.x], False)
            signer = DSS.new(key, 'deterministic-rfc6979')

            hash_obj = sig.module.new(sig.message)
            result = signer.sign(hash_obj)
            self.assertEqual(sig.result, result)


class Det_ECDSA_Tests(unittest.TestCase):

    key_priv = ECC.construct(curve="P-256", d=0xC9AFA9D845BA75166B5C215767B1D6934E50C3DB36E89B127B8A622B120F6721)
    key_pub = key_priv.public_key()

    # This is a sequence of items:
    # message, k, r, s, hash module
    # taken from RFC6979
    signatures_ = (
        (
            "sample",
            "882905F1227FD620FBF2ABF21244F0BA83D0DC3A9103DBBEE43A1FB858109DB4",
            "61340C88C3AAEBEB4F6D667F672CA9759A6CCAA9FA8811313039EE4A35471D32",
            "6D7F147DAC089441BB2E2FE8F7A3FA264B9C475098FDCF6E00D7C996E1B8B7EB",
            SHA1
        ),
        (
            "sample",
            "103F90EE9DC52E5E7FB5132B7033C63066D194321491862059967C715985D473",
            "53B2FFF5D1752B2C689DF257C04C40A587FABABB3F6FC2702F1343AF7CA9AA3F",
            "B9AFB64FDC03DC1A131C7D2386D11E349F070AA432A4ACC918BEA988BF75C74C",
            SHA224
        ),
        (
            "sample",
            "A6E3C57DD01ABE90086538398355DD4C3B17AA873382B0F24D6129493D8AAD60",
            "EFD48B2AACB6A8FD1140DD9CD45E81D69D2C877B56AAF991C34D0EA84EAF3716",
            "F7CB1C942D657C41D436C7A1B6E29F65F3E900DBB9AFF4064DC4AB2F843ACDA8",
            SHA256
        ),
        (
            "sample",
            "09F634B188CEFD98E7EC88B1AA9852D734D0BC272F7D2A47DECC6EBEB375AAD4",
            "0EAFEA039B20E9B42309FB1D89E213057CBF973DC0CFC8F129EDDDC800EF7719",
            "4861F0491E6998B9455193E34E7B0D284DDD7149A74B95B9261F13ABDE940954",
            SHA384
        ),
        (
            "sample",
            "5FA81C63109BADB88C1F367B47DA606DA28CAD69AA22C4FE6AD7DF73A7173AA5",
            "8496A60B5E9B47C825488827E0495B0E3FA109EC4568FD3F8D1097678EB97F00",
            "2362AB1ADBE2B8ADF9CB9EDAB740EA6049C028114F2460F96554F61FAE3302FE",
            SHA512
        ),
        (
            "test",
            "8C9520267C55D6B980DF741E56B4ADEE114D84FBFA2E62137954164028632A2E",
            "0CBCC86FD6ABD1D99E703E1EC50069EE5C0B4BA4B9AC60E409E8EC5910D81A89",
            "01B9D7B73DFAA60D5651EC4591A0136F87653E0FD780C3B1BC872FFDEAE479B1",
            SHA1
        ),
        (
            "test",
            "669F4426F2688B8BE0DB3A6BD1989BDAEFFF84B649EEB84F3DD26080F667FAA7",
            "C37EDB6F0AE79D47C3C27E962FA269BB4F441770357E114EE511F662EC34A692",
            "C820053A05791E521FCAAD6042D40AEA1D6B1A540138558F47D0719800E18F2D",
            SHA224
        ),
        (
            "test",
            "D16B6AE827F17175E040871A1C7EC3500192C4C92677336EC2537ACAEE0008E0",
            "F1ABB023518351CD71D881567B1EA663ED3EFCF6C5132B354F28D3B0B7D38367",
            "019F4113742A2B14BD25926B49C649155F267E60D3814B4C0CC84250E46F0083",
            SHA256
        ),
        (
            "test",
            "16AEFFA357260B04B1DD199693960740066C1A8F3E8EDD79070AA914D361B3B8",
            "83910E8B48BB0C74244EBDF7F07A1C5413D61472BD941EF3920E623FBCCEBEB6",
            "8DDBEC54CF8CD5874883841D712142A56A8D0F218F5003CB0296B6B509619F2C",
            SHA384
        ),
        (
            "test",
            "6915D11632ACA3C40D5D51C08DAF9C555933819548784480E93499000D9F0B7F",
            "461D93F31B6540894788FD206C07CFA0CC35F46FA3C91816FFF1040AD1581A04",
            "39AF9F15DE0DB8D97E72719C74820D304CE5226E32DEDAE67519E840D1194E55",
            SHA512
        )
    )

    signatures = []
    for a, b, c, d, e in signatures_:
        new_tv = (tobytes(a), unhexlify(b), unhexlify(c), unhexlify(d), e)
        signatures.append(new_tv)

    def shortDescription(self):
        return "Deterministic ECDSA Tests"

    def test_loopback(self):
        hashed_msg = SHA512.new(b("test"))
        signer = DSS.new(self.key_priv, 'deterministic-rfc6979')
        signature = signer.sign(hashed_msg)

        verifier = DSS.new(self.key_pub, 'deterministic-rfc6979')
        verifier.verify(hashed_msg, signature)

    def test_data_rfc6979(self):
        signer = DSS.new(self.key_priv, 'deterministic-rfc6979')
        for message, k, r, s, module  in self.signatures:
            hash_obj = module.new(message)
            result = signer.sign(hash_obj)
            self.assertEqual(r + s, result)


class TestVectorsDSAWycheproof(unittest.TestCase):

    def __init__(self, wycheproof_warnings):
        unittest.TestCase.__init__(self)
        self._wycheproof_warnings = wycheproof_warnings
        self._id = "None"

    def setUp(self):
        comps = "Crypto.SelfTest.Signature.test_vectors.wycheproof".split(".")
        with open(pycryptodome_filename(comps, "dsa_test.json"), "rt") as file_in:
            tv_tree = json.load(file_in)

        class TestVector(object):
            pass
        self.tv = []

        for group in tv_tree['testGroups']:
            key = DSA.import_key(group['keyPem'])
            hash_name = group['sha']
            if hash_name == "SHA-256":
                hash_module = SHA256
            elif hash_name == "SHA-224":
                hash_module = SHA224
            elif hash_name == "SHA-1":
                hash_module = SHA1
            else:
                assert False
            assert group['type'] == "DSAVer"
            
            for test in group['tests']:
                tv = TestVector()
                
                tv.id = test['tcId']
                tv.comment = test['comment']
                for attr in 'msg', 'sig':
                    setattr(tv, attr, unhexlify(test[attr]))
                tv.key = key
                tv.hash_module = hash_module
                tv.valid = test['result'] != "invalid"
                tv.warning = test['result'] == "acceptable"
                self.tv.append(tv)

    def shortDescription(self):
        return self._id

    def warn(self, tv):
        if tv.warning and self._wycheproof_warnings:
            import warnings
            warnings.warn("Wycheproof warning: %s (%s)" % (self._id, tv.comment))

    def test_verify(self, tv):
        self._id = "Wycheproof DSA Test #" + str(tv.id)
        
        hashed_msg = tv.hash_module.new(tv.msg)
        signer = DSS.new(tv.key, 'fips-186-3', encoding='der')
        try:
            signature = signer.verify(hashed_msg, tv.sig)
        except ValueError as e:
            if tv.warning:
                return
            assert not tv.valid
        else:
            assert tv.valid
            self.warn(tv)

    def runTest(self):
        for tv in self.tv:
            self.test_verify(tv)


class TestVectorsECDSAWycheproof(unittest.TestCase):

    def __init__(self, wycheproof_warnings):
        unittest.TestCase.__init__(self)
        self._wycheproof_warnings = wycheproof_warnings
        self._id = "None"

    class TestVector(object):
        pass

    def add_tests(self, filename):
        comps = "Crypto.SelfTest.Signature.test_vectors.wycheproof".split(".")
        with open(pycryptodome_filename(comps, filename), "rt") as file_in:
            tv_tree = json.load(file_in)

        for group in tv_tree['testGroups']:
            
            try:
                key = ECC.import_key(group['keyPem'])
            except ValueError:
                continue
            
            hash_name = group['sha']
            if hash_name == "SHA-256":
                hash_module = SHA256
            elif hash_name == "SHA-224":
                hash_module = SHA224
            elif hash_name == "SHA-1":
                hash_module = SHA1
            else:
                assert False
            assert group['type'] == "ECDSAVer"
            
            for test in group['tests']:
                tv = TestVector()
                
                tv.id = test['tcId']
                tv.comment = test['comment']
                for attr in 'msg', 'sig':
                    setattr(tv, attr, unhexlify(test[attr]))
                tv.key = key
                tv.hash_module = hash_module
                tv.valid = test['result'] != "invalid"
                tv.warning = test['result'] == "acceptable"
                self.tv.append(tv)

    def setUp(self):
        self.tv = []
        self.add_tests("ecdsa_test.json")
        self.add_tests("ecdsa_secp256r1_sha256_test.json")

    def shortDescription(self):
        return self._id

    def warn(self, tv):
        if tv.warning and self._wycheproof_warnings:
            import warnings
            warnings.warn("Wycheproof warning: %s (%s)" % (self._id, tv.comment))

    def test_verify(self, tv):
        self._id = "Wycheproof ECDSA Test #%d (%s)" % (tv.id, tv.comment)

        hashed_msg = tv.hash_module.new(tv.msg)
        signer = DSS.new(tv.key, 'fips-186-3', encoding='der')
        try:
            signature = signer.verify(hashed_msg, tv.sig)
        except ValueError as e:
            if tv.warning:
                return
            if tv.comment == "k*G has a large x-coordinate":
                return
            assert not tv.valid
        else:
            assert tv.valid
            self.warn(tv)

    def runTest(self):
        for tv in self.tv:
            self.test_verify(tv)


def get_tests(config={}):
    wycheproof_warnings = config.get('wycheproof_warnings')

    tests = []
    tests += list_test_cases(FIPS_DSA_Tests)
    tests += list_test_cases(FIPS_ECDSA_Tests)
    tests += list_test_cases(Det_DSA_Tests)
    tests += list_test_cases(Det_ECDSA_Tests)

    if config.get('slow_tests'):
        tests += list_test_cases(FIPS_DSA_Tests_KAT)
        tests += list_test_cases(FIPS_ECDSA_Tests_KAT)

    tests += [ TestVectorsDSAWycheproof(wycheproof_warnings) ]
    tests += [ TestVectorsECDSAWycheproof(wycheproof_warnings) ]

    return tests


if __name__ == '__main__':
    suite = lambda: unittest.TestSuite(get_tests())
    unittest.main(defaultTest='suite')
