# -*- coding: utf-8 -*-
#
# Hash/CMAC.py - Implements the CMAC algorithm
#
# ===================================================================
# The contents of this file are dedicated to the public domain.  To
# the extent that dedication to the public domain is not available,
# everyone is granted a worldwide, perpetual, royalty-free,
# non-exclusive license to exercise all rights associated with the
# contents of this file for any purpose whatsoever.
# No rights are reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ===================================================================

import sys

from Crypto.Util.py3compat import bord, tobytes, _copy_bytes

from binascii import unhexlify

from Crypto.Hash import BLAKE2s
from Crypto.Util.strxor import strxor
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Random import get_random_bytes

# The size of the authentication tag produced by the MAC.
digest_size = None


def _shift_bytes(bs, xor_lsb=0):
    num = (bytes_to_long(bs) << 1) ^ xor_lsb
    return long_to_bytes(num, len(bs))[-len(bs):]


class CMAC(object):
    """A CMAC hash object.
    Do not instantiate directly. Use the :func:`new` function.

    :ivar digest_size: the size in bytes of the resulting MAC tag
    :vartype digest_size: integer
    """

    digest_size = None

    def __init__(self, key, msg, ciphermod, cipher_params, mac_len):

        if ciphermod is None:
            raise TypeError("ciphermod must be specified (try AES)")

        self._key = _copy_bytes(None, None, key)
        self._factory = ciphermod
        if cipher_params is None:
            self._cipher_params = {}
        else:
            self._cipher_params = dict(cipher_params)
        self._mac_len = mac_len or ciphermod.block_size

        if self._mac_len < 4:
            raise ValueError("MAC tag length must be at least 4 bytes long")
        if self._mac_len > ciphermod.block_size:
            raise ValueError("MAC tag length cannot be larger than a cipher block (%d) bytes" % ciphermod.block_size)

        # Section 5.3 of NIST SP 800 38B and Appendix B
        if ciphermod.block_size == 8:
            const_Rb = 0x1B
            self._max_size = 8 * (2 ** 21)
        elif ciphermod.block_size == 16:
            const_Rb = 0x87
            self._max_size = 16 * (2 ** 48)
        else:
            raise TypeError("CMAC requires a cipher with a block size"
                            "of 8 or 16 bytes, not %d" %
                            (ciphermod.block_size,))

        # Size of the final MAC tag, in bytes
        self.digest_size = ciphermod.block_size
        self._mac_tag = None

        # Compute sub-keys
        zero_block = b'\x00' * ciphermod.block_size
        cipher = ciphermod.new(key,
                               ciphermod.MODE_ECB,
                               **self._cipher_params)
        l = cipher.encrypt(zero_block)
        if bord(l[0]) & 0x80:
            self._k1 = _shift_bytes(l, const_Rb)
        else:
            self._k1 = _shift_bytes(l)
        if bord(self._k1[0]) & 0x80:
            self._k2 = _shift_bytes(self._k1, const_Rb)
        else:
            self._k2 = _shift_bytes(self._k1)

        # Initialize CBC cipher with zero IV
        self._cbc = ciphermod.new(key,
                                  ciphermod.MODE_CBC,
                                  zero_block,
                                  **self._cipher_params)

        # Cache for outstanding data to authenticate
        self._cache = b""

        # Last two pieces of ciphertext produced
        self._last_ct = self._last_pt = zero_block
        self._before_last_ct = None

        # Counter for total message size
        self._data_size = 0

        if msg:
            self.update(msg)

    def update(self, msg):
        """Authenticate the next chunk of message.

        Args:
            data (byte string/byte array/memoryview): The next chunk of data
        """

        # Mutable values must be copied if cached

        self._data_size += len(msg)

        if len(self._cache) > 0:
            filler = min(self.digest_size - len(self._cache), len(msg))
            self._cache += msg[:filler]

            if len(self._cache) < self.digest_size:
                return self

            msg = msg[filler:]
            self._update(self._cache)
            self._cache = b""

        update_len, remain = divmod(len(msg), self.digest_size)
        update_len *= self.digest_size
        if remain > 0:
            self._update(msg[:update_len])
            self._cache = _copy_bytes(update_len, None, msg)
        else:
            self._update(msg)
            self._cache = b""
        return self

    def _update(self, data_block):
        """Update a block aligned to the block boundary"""

        if len(data_block) == 0:
            return

        assert len(data_block) % self.digest_size == 0

        ct = self._cbc.encrypt(data_block)

        if len(data_block) == self.digest_size:
            self._before_last_ct = self._last_ct
        else:
            self._before_last_ct = ct[-self.digest_size * 2:-self.digest_size]
        self._last_ct = ct[-self.digest_size:]

        # data_block can mutable
        self._last_pt = _copy_bytes(-self.digest_size, None, data_block)

    def copy(self):
        """Return a copy ("clone") of the CMAC object.

        The copy will have the same internal state as the original CMAC
        object.
        This can be used to efficiently compute the MAC tag of byte
        strings that share a common initial substring.

        :return: An :class:`CMAC`
        """

        obj = CMAC(self._key,
                   b"",
                   ciphermod=self._factory,
                   cipher_params=self._cipher_params,
                   mac_len=self._mac_len)

        obj._cbc = self._factory.new(self._key,
                                     self._factory.MODE_CBC,
                                     self._last_ct,
                                     **self._cipher_params)
        for m in ['_mac_tag', '_last_ct', '_before_last_ct', '_cache',
                  '_data_size', '_max_size']:
            setattr(obj, m, getattr(self, m))
        return obj

    def digest(self):
        """Return the **binary** (non-printable) MAC tag of the message
        that has been authenticated so far.

        :return: The MAC tag, computed over the data processed so far.
                 Binary form.
        :rtype: byte string
        """

        if self._mac_tag is not None:
            return self._mac_tag[:self._mac_len]

        if self._data_size > self._max_size:
            raise ValueError("MAC is unsafe for this message")

        if len(self._cache) == 0 and self._before_last_ct is not None:
            # Last block was full
            pt = strxor(strxor(self._before_last_ct, self._k1), self._last_pt)
        else:
            # Last block is partial (or message length is zero)
            ext = self._cache + b'\x80' +\
                    b'\x00' * (self.digest_size - len(self._cache) - 1)
            pt = strxor(strxor(self._last_ct, self._k2), ext)

        cipher = self._factory.new(self._key,
                                   self._factory.MODE_ECB,
                                   **self._cipher_params)
        self._mac_tag = cipher.encrypt(pt)

        return self._mac_tag[:self._mac_len]

    def hexdigest(self):
        """Return the **printable** MAC tag of the message authenticated so far.

        :return: The MAC tag, computed over the data processed so far.
                 Hexadecimal encoded.
        :rtype: string
        """

        return "".join(["%02x" % bord(x)
                        for x in tuple(self.digest())])

    def verify(self, mac_tag):
        """Verify that a given **binary** MAC (computed by another party)
        is valid.

        Args:
          mac_tag (byte string/byte array/memoryview): the expected MAC of the message.

        Raises:
            ValueError: if the MAC does not match. It means that the message
                has been tampered with or that the MAC key is incorrect.
        """

        secret = get_random_bytes(16)

        mac1 = BLAKE2s.new(digest_bits=160, key=secret, data=mac_tag)
        mac2 = BLAKE2s.new(digest_bits=160, key=secret, data=self.digest())

        if mac1.digest() != mac2.digest():
            raise ValueError("MAC check failed")

    def hexverify(self, hex_mac_tag):
        """Return the **printable** MAC tag of the message authenticated so far.

        :return: The MAC tag, computed over the data processed so far.
                 Hexadecimal encoded.
        :rtype: string
        """

        self.verify(unhexlify(tobytes(hex_mac_tag)))


def new(key, msg=None, ciphermod=None, cipher_params=None, mac_len=None):
    """Create a new MAC object.

    Args:
        key (byte string/byte array/memoryview):
            key for the CMAC object.
            The key must be valid for the underlying cipher algorithm.
            For instance, it must be 16 bytes long for AES-128.
        ciphermod (module):
            A cipher module from :mod:`Crypto.Cipher`.
            The cipher's block size has to be 128 bits,
            like :mod:`Crypto.Cipher.AES`, to reduce the probability
            of collisions.
        msg (byte string/byte array/memoryview):
            Optional. The very first chunk of the message to authenticate.
            It is equivalent to an early call to `CMAC.update`. Optional.
        cipher_params (dict):
            Optional. A set of parameters to use when instantiating a cipher
            object.
        mac_len (integer):
            Length of the MAC, in bytes.
            It must be at least 4 bytes long.
            The default (and recommended) length matches the size of a cipher block.

    Returns:
        A :class:`CMAC` object
    """

    return CMAC(key, msg, ciphermod, cipher_params, mac_len)
