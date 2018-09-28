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

from Crypto.Random import get_random_bytes

from Crypto.Util.py3compat import _copy_bytes
from Crypto.Util._raw_api import (load_pycryptodome_raw_lib,
                                  create_string_buffer,
                                  get_raw_buffer, VoidPointer,
                                  SmartPointer, c_size_t,
                                  c_uint8_ptr, c_ulong)

_raw_chacha20_lib = load_pycryptodome_raw_lib("Crypto.Cipher._chacha20",
                    """
                    int chacha20_init(void **pState,
                                      const uint8_t *key,
                                      size_t keySize,
                                      const uint8_t *nonce,
                                      size_t nonceSize);

                    int chacha20_destroy(void *state);

                    int chacha20_encrypt(void *state,
                                         const uint8_t in[],
                                         uint8_t out[],
                                         size_t len);

                    int chacha20_seek(void *state,
                                      unsigned long block_high,
                                      unsigned long block_low,
                                      unsigned offset);
                    """)


class ChaCha20Cipher:
    """ChaCha20 cipher object. Do not create it directly. Use :py:func:`new` instead.

    :var nonce: The nonce with length 8 or 12
    :vartype nonce: byte string
    """

    block_size = 1

    def __init__(self, key, nonce):
        """Initialize a ChaCha20 cipher object

        See also `new()` at the module level."""

        self.nonce = _copy_bytes(None, None, nonce)

        self._next = ( self.encrypt, self.decrypt )
        self._state = VoidPointer()
        result = _raw_chacha20_lib.chacha20_init(
                        self._state.address_of(),
                        c_uint8_ptr(key),
                        c_size_t(len(key)),
                        self.nonce,
                        c_size_t(len(nonce)))
        if result:
            raise ValueError("Error %d instantiating a ChaCha20 cipher")
        self._state = SmartPointer(self._state.get(),
                                   _raw_chacha20_lib.chacha20_destroy)

    def encrypt(self, plaintext):
        """Encrypt a piece of data.

        :param plaintext: The data to encrypt, of any size.
        :type plaintext: bytes, bytearray, memoryview
        :returns: the encrypted byte string, of equal length as the
          plaintext.
        """

        if self.encrypt not in self._next:
            raise TypeError("Cipher object can only be used for decryption")
        self._next = ( self.encrypt, )
        return self._encrypt(plaintext)

    def _encrypt(self, plaintext):
        """Encrypt without FSM checks"""

        ciphertext = create_string_buffer(len(plaintext))
        result = _raw_chacha20_lib.chacha20_encrypt(
                                         self._state.get(),
                                         c_uint8_ptr(plaintext),
                                         ciphertext,
                                         c_size_t(len(plaintext)))
        if result:
            raise ValueError("Error %d while encrypting with ChaCha20" % result)
        return get_raw_buffer(ciphertext)

    def decrypt(self, ciphertext):
        """Decrypt a piece of data.

        :param ciphertext: The data to decrypt, of any size.
        :type ciphertext: bytes, bytearray, memoryview
        :returns: the decrypted byte string, of equal length as the
          ciphertext.
        """

        if self.decrypt not in self._next:
            raise TypeError("Cipher object can only be used for encryption")
        self._next = ( self.decrypt, )

        try:
            return self._encrypt(ciphertext)
        except ValueError as e:
            raise ValueError(str(e).replace("enc", "dec"))

    def seek(self, position):
        """Seek to a certain position in the key stream.

        :param integer position:
            The absolute position within the key stream, in bytes.
        """

        position, offset = divmod(position, 64)
        block_low = position & 0xFFFFFFFF
        block_high = position >> 32

        result = _raw_chacha20_lib.chacha20_seek(
                                                 self._state.get(),
                                                 c_ulong(block_high),
                                                 c_ulong(block_low),
                                                 offset
                                                 )
        if result:
            raise ValueError("Error %d while seeking with ChaCha20" % result)


def new(**kwargs):
    """Create a new ChaCha20 cipher

    :keyword key: The secret key to use. It must be 32 bytes long.
    :type key: byte string

    :keyword nonce:
        A mandatory value that must never be reused for any other encryption
        done with this key. It must be 8 or 12 bytes long.

        If not provided, a random 8-byte string will be generated
        (you can read it back via the ``nonce`` attribute of the returned object).
    :type nonce: bytes, bytearray, memoryview

    :Return: a :class:`Crypto.Cipher.ChaCha20.ChaCha20Cipher` object
    """

    try:
        key = kwargs.pop("key")
    except KeyError as e:
        raise TypeError("Missing parameter %s" % e)

    nonce = kwargs.pop("nonce", None)
    if nonce is None:
        nonce = get_random_bytes(8)

    if len(key) != 32:
        raise ValueError("ChaCha20 key must be 32 bytes long")
    if len(nonce) not in (8, 12):
        raise ValueError("ChaCha20 nonce must be 8 or 12 bytes long")

    if kwargs:
        raise TypeError("Unknown parameters: " + str(kwargs))

    return ChaCha20Cipher(key, nonce)

# Size of a data block (in bytes)
block_size = 1

# Size of a key (in bytes)
key_size = 32
