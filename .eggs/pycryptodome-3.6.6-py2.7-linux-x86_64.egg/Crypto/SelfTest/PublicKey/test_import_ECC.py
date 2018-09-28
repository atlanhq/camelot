# ===================================================================
#
# Copyright (c) 2015, Legrandin <helderijs@gmail.com>
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
from Crypto.SelfTest.st_common import list_test_cases
from Crypto.Util._file_system import pycryptodome_filename
from Crypto.Util.py3compat import b, unhexlify, bord, tostr
from Crypto.Util.number import bytes_to_long
from Crypto.Hash import SHAKE128

from Crypto.PublicKey import ECC

def load_file(filename, mode="rb"):
    comps = [ "Crypto", "SelfTest", "PublicKey", "test_vectors", "ECC" ]
    with open(pycryptodome_filename(comps, filename), mode) as fd:
        return fd.read()


def compact(lines):
    ext = b("").join(lines)
    return unhexlify(tostr(ext).replace(" ", "").replace(":", ""))


def create_ref_keys():
    key_lines = load_file("ecc_p256.txt").splitlines()
    private_key_d = bytes_to_long(compact(key_lines[2:5]))
    public_key_xy = compact(key_lines[6:11])
    assert bord(public_key_xy[0]) == 4  # Uncompressed
    public_key_x = bytes_to_long(public_key_xy[1:33])
    public_key_y = bytes_to_long(public_key_xy[33:])

    return (ECC.construct(curve="P-256", d=private_key_d),
            ECC.construct(curve="P-256", point_x=public_key_x, point_y=public_key_y))


# Create reference key pair
ref_private, ref_public = create_ref_keys()


def get_fixed_prng():
        return SHAKE128.new().update(b("SEED")).read


class TestImport(unittest.TestCase):

    def test_import_public_der(self):
        key_file = load_file("ecc_p256_public.der")

        key = ECC._import_subjectPublicKeyInfo(key_file)
        self.assertEqual(ref_public, key)

        key = ECC._import_der(key_file, None)
        self.assertEqual(ref_public, key)

        key = ECC.import_key(key_file)
        self.assertEqual(ref_public, key)

    def test_import_private_der(self):
        key_file = load_file("ecc_p256_private.der")

        key = ECC._import_private_der(key_file, None)
        self.assertEqual(ref_private, key)

        key = ECC._import_der(key_file, None)
        self.assertEqual(ref_private, key)

        key = ECC.import_key(key_file)
        self.assertEqual(ref_private, key)

    def test_import_private_pkcs8_clear(self):
        key_file = load_file("ecc_p256_private_p8_clear.der")

        key = ECC._import_der(key_file, None)
        self.assertEqual(ref_private, key)

        key = ECC.import_key(key_file)
        self.assertEqual(ref_private, key)

    def test_import_private_pkcs8_in_pem_clear(self):
        key_file = load_file("ecc_p256_private_p8_clear.pem")

        key = ECC.import_key(key_file)
        self.assertEqual(ref_private, key)

    def test_import_private_pkcs8_encrypted_1(self):
        key_file = load_file("ecc_p256_private_p8.der")

        key = ECC._import_der(key_file, "secret")
        self.assertEqual(ref_private, key)

        key = ECC.import_key(key_file, "secret")
        self.assertEqual(ref_private, key)

    def test_import_private_pkcs8_encrypted_2(self):
        key_file = load_file("ecc_p256_private_p8.pem")

        key = ECC.import_key(key_file, "secret")
        self.assertEqual(ref_private, key)

    def test_import_x509_der(self):
        key_file = load_file("ecc_p256_x509.der")

        key = ECC._import_der(key_file, None)
        self.assertEqual(ref_public, key)

        key = ECC.import_key(key_file)
        self.assertEqual(ref_public, key)

    def test_import_public_pem(self):
        key_file = load_file("ecc_p256_public.pem")

        key = ECC.import_key(key_file)
        self.assertEqual(ref_public, key)

    def test_import_private_pem(self):
        key_file = load_file("ecc_p256_private.pem")

        key = ECC.import_key(key_file)
        self.assertEqual(ref_private, key)

    def test_import_private_pem_encrypted(self):
        for algo in "des3", : # TODO: , "aes128", "aes192", "aes256_gcm":
            key_file = load_file("ecc_p256_private_enc_%s.pem" % algo)

            key = ECC.import_key(key_file, "secret")
            self.assertEqual(ref_private, key)

            key = ECC.import_key(tostr(key_file), b("secret"))
            self.assertEqual(ref_private, key)

    def test_import_x509_pem(self):
        key_file = load_file("ecc_p256_x509.pem")

        key = ECC.import_key(key_file)
        self.assertEqual(ref_public, key)

    def test_import_openssh(self):
        key_file = load_file("ecc_p256_public_openssh.txt")

        key = ECC._import_openssh(key_file)
        self.assertEqual(ref_public, key)

        key = ECC.import_key(key_file)
        self.assertEqual(ref_public, key)


class TestExport(unittest.TestCase):

    def test_export_public_der_uncompressed(self):
        key_file = load_file("ecc_p256_public.der")

        encoded = ref_public._export_subjectPublicKeyInfo(False)
        self.assertEqual(key_file, encoded)

        encoded = ref_public.export_key(format="DER")
        self.assertEqual(key_file, encoded)

        encoded = ref_public.export_key(format="DER", compress=False)
        self.assertEqual(key_file, encoded)

    def test_export_public_der_compressed(self):
        key_file = load_file("ecc_p256_public.der")
        pub_key = ECC.import_key(key_file)
        key_file_compressed = pub_key.export_key(format="DER", compress=True)

        key_file_compressed_ref = load_file("ecc_p256_public_compressed.der")
        self.assertEqual(key_file_compressed, key_file_compressed_ref)

    def test_export_private_der(self):
        key_file = load_file("ecc_p256_private.der")

        encoded = ref_private._export_private_der()
        self.assertEqual(key_file, encoded)

        # ---

        encoded = ref_private.export_key(format="DER", use_pkcs8=False)
        self.assertEqual(key_file, encoded)

    def test_export_private_pkcs8_clear(self):
        key_file = load_file("ecc_p256_private_p8_clear.der")

        encoded = ref_private._export_pkcs8()
        self.assertEqual(key_file, encoded)

        # ---

        encoded = ref_private.export_key(format="DER")
        self.assertEqual(key_file, encoded)

    def test_export_private_pkcs8_encrypted(self):
        encoded = ref_private._export_pkcs8(passphrase="secret",
                                            protection="PBKDF2WithHMAC-SHA1AndAES128-CBC")

        # This should prove that the output is password-protected
        self.assertRaises(ValueError, ECC._import_pkcs8, encoded, None)

        decoded = ECC._import_pkcs8(encoded, "secret")
        self.assertEqual(ref_private, decoded)

        # ---

        encoded = ref_private.export_key(format="DER",
                                         passphrase="secret",
                                         protection="PBKDF2WithHMAC-SHA1AndAES128-CBC")
        decoded = ECC.import_key(encoded, "secret")
        self.assertEqual(ref_private, decoded)

    def test_export_public_pem_uncompressed(self):
        key_file = load_file("ecc_p256_public.pem", "rt").strip()

        encoded = ref_private._export_public_pem(False)
        self.assertEqual(key_file, encoded)

        # ---

        encoded = ref_public.export_key(format="PEM")
        self.assertEqual(key_file, encoded)

        encoded = ref_public.export_key(format="PEM", compress=False)
        self.assertEqual(key_file, encoded)

    def test_export_public_pem_compressed(self):
        key_file = load_file("ecc_p256_public.pem", "rt").strip()
        pub_key = ECC.import_key(key_file)

        key_file_compressed = pub_key.export_key(format="PEM", compress=True)
        key_file_compressed_ref = load_file("ecc_p256_public_compressed.pem", "rt").strip()

        self.assertEqual(key_file_compressed, key_file_compressed_ref)

    def test_export_private_pem_clear(self):
        key_file = load_file("ecc_p256_private.pem", "rt").strip()

        encoded = ref_private._export_private_pem(None)
        self.assertEqual(key_file, encoded)

        # ---

        encoded = ref_private.export_key(format="PEM", use_pkcs8=False)
        self.assertEqual(key_file, encoded)

    def test_export_private_pem_encrypted(self):
        encoded = ref_private._export_private_pem(passphrase=b("secret"))

        # This should prove that the output is password-protected
        self.assertRaises(ValueError, ECC.import_key, encoded)

        assert "EC PRIVATE KEY" in encoded

        decoded = ECC.import_key(encoded, "secret")
        self.assertEqual(ref_private, decoded)

        # ---

        encoded = ref_private.export_key(format="PEM",
                                         passphrase="secret",
                                         use_pkcs8=False)
        decoded = ECC.import_key(encoded, "secret")
        self.assertEqual(ref_private, decoded)

    def test_export_private_pkcs8_and_pem_1(self):
        # PKCS8 inside PEM with both unencrypted
        key_file = load_file("ecc_p256_private_p8_clear.pem", "rt").strip()

        encoded = ref_private._export_private_clear_pkcs8_in_clear_pem()
        self.assertEqual(key_file, encoded)

        # ---

        encoded = ref_private.export_key(format="PEM")
        self.assertEqual(key_file, encoded)

    def test_export_private_pkcs8_and_pem_2(self):
        # PKCS8 inside PEM with PKCS8 encryption
        encoded = ref_private._export_private_encrypted_pkcs8_in_clear_pem("secret",
                              protection="PBKDF2WithHMAC-SHA1AndAES128-CBC")

        # This should prove that the output is password-protected
        self.assertRaises(ValueError, ECC.import_key, encoded)

        assert "ENCRYPTED PRIVATE KEY" in encoded

        decoded = ECC.import_key(encoded, "secret")
        self.assertEqual(ref_private, decoded)

        # ---

        encoded = ref_private.export_key(format="PEM",
                                         passphrase="secret",
                                         protection="PBKDF2WithHMAC-SHA1AndAES128-CBC")
        decoded = ECC.import_key(encoded, "secret")
        self.assertEqual(ref_private, decoded)

    def test_export_openssh_uncompressed(self):
        key_file = load_file("ecc_p256_public_openssh.txt", "rt")

        encoded = ref_public._export_openssh(False)
        self.assertEquals(key_file, encoded)

        # ---

        encoded = ref_public.export_key(format="OpenSSH")
        self.assertEquals(key_file, encoded)

        encoded = ref_public.export_key(format="OpenSSH", compress=False)
        self.assertEquals(key_file, encoded)

    def test_export_openssh_compressed(self):
        key_file = load_file("ecc_p256_public_openssh.txt", "rt")
        pub_key = ECC.import_key(key_file)

        key_file_compressed = pub_key.export_key(format="OpenSSH", compress=True)
        assert len(key_file) > len(key_file_compressed)
        self.assertEquals(pub_key, ECC.import_key(key_file_compressed))

    def test_prng(self):
        # Test that password-protected containers use the provided PRNG
        encoded1 = ref_private.export_key(format="PEM",
                                          passphrase="secret",
                                          protection="PBKDF2WithHMAC-SHA1AndAES128-CBC",
                                          randfunc=get_fixed_prng())
        encoded2 = ref_private.export_key(format="PEM",
                                          passphrase="secret",
                                          protection="PBKDF2WithHMAC-SHA1AndAES128-CBC",
                                          randfunc=get_fixed_prng())
        self.assertEquals(encoded1, encoded2)

        # ---

        encoded1 = ref_private.export_key(format="PEM",
                                          use_pkcs8=False,
                                          passphrase="secret",
                                          randfunc=get_fixed_prng())
        encoded2 = ref_private.export_key(format="PEM",
                                          use_pkcs8=False,
                                          passphrase="secret",
                                          randfunc=get_fixed_prng())
        self.assertEquals(encoded1, encoded2)

    def test_byte_or_string_passphrase(self):
        encoded1 = ref_private.export_key(format="PEM",
                                          use_pkcs8=False,
                                          passphrase="secret",
                                          randfunc=get_fixed_prng())
        encoded2 = ref_private.export_key(format="PEM",
                                          use_pkcs8=False,
                                          passphrase=b("secret"),
                                          randfunc=get_fixed_prng())
        self.assertEquals(encoded1, encoded2)

    def test_error_params1(self):
        # Unknown format
        self.assertRaises(ValueError, ref_private.export_key, format="XXX")

        # Missing 'protection' parameter when PKCS#8 is used
        ref_private.export_key(format="PEM", passphrase="secret",
                               use_pkcs8=False)
        self.assertRaises(ValueError, ref_private.export_key, format="PEM",
                                      passphrase="secret")

        # DER format but no PKCS#8
        self.assertRaises(ValueError, ref_private.export_key, format="DER",
                                      passphrase="secret",
                                      use_pkcs8=False,
                                      protection="PBKDF2WithHMAC-SHA1AndAES128-CBC")

        # Incorrect parameters for public keys
        self.assertRaises(ValueError, ref_public.export_key, format="DER",
                          use_pkcs8=False)

        # Empty password
        self.assertRaises(ValueError, ref_private.export_key, format="PEM",
                                      passphrase="", use_pkcs8=False)
        self.assertRaises(ValueError, ref_private.export_key, format="PEM",
                                      passphrase="",
                                      protection="PBKDF2WithHMAC-SHA1AndAES128-CBC")

        # No private keys with OpenSSH
        self.assertRaises(ValueError, ref_private.export_key, format="OpenSSH",
                                      passphrase="secret")

    def test_unsupported_curve(self):

        # openssl ecparam -name secp224r1 -genkey -noout -out strange-curve.pem -conv_form uncompressed
        curve = """-----BEGIN EC PRIVATE KEY-----
MGgCAQEEHEi7xTHW+5oT8wgpjoEKV7uwMuY8rt2YUZe4j1SgBwYFK4EEACGhPAM6
AATJgfOG+Bnki8robpNM8MtArji43GU9up4B0x9sVhqB+fZP+hXgV9ITN7YX4E/k
gVnJp9EBND/tHQ==
-----END EC PRIVATE KEY-----"""

        from Crypto.PublicKey.ECC import UnsupportedEccFeature
        try:
            ECC.import_key(curve)
        except UnsupportedEccFeature as uef:
            assert("1.3.132.0.33" in str(uef))
        else:
            assert(False)

    def test_compressed_curve(self):

        # Compressed P-256 curve (Y-point is even)
        pem1 = """-----BEGIN EC PRIVATE KEY-----
        MFcCAQEEIHTuc09jC51xXomV6MVCDN+DpAAvSmaJWZPTEHM6D5H1oAoGCCqGSM49
        AwEHoSQDIgACWFuGbHe8yJ43rir7PMTE9w8vHz0BSpXHq90Xi7/s+a0=
        -----END EC PRIVATE KEY-----"""

        # Compressed P-256 curve (Y-point is odd)
        pem2 = """-----BEGIN EC PRIVATE KEY-----
        MFcCAQEEIFggiPN9SQP+FAPTCPp08fRUz7rHp2qNBRcBJ1DXhb3ZoAoGCCqGSM49
        AwEHoSQDIgADLpph1trTIlVfa8NJvlMUPyWvL+wP+pW3BJITUL/wj9A=
        -----END EC PRIVATE KEY-----"""

        key1 = ECC.import_key(pem1)
        low16 = int(key1.pointQ.y % 65536)
        self.assertEqual(low16, 0xA6FC)

        key2 = ECC.import_key(pem2)
        low16 = int(key2.pointQ.y % 65536)
        self.assertEqual(low16, 0x6E57)


def get_tests(config={}):
    tests = []
    tests += list_test_cases(TestImport)
    tests += list_test_cases(TestExport)
    return tests

if __name__ == '__main__':
    suite = lambda: unittest.TestSuite(get_tests())
    unittest.main(defaultTest='suite')
