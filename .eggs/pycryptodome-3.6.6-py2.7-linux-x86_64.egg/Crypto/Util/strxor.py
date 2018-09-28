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

from Crypto.Util._raw_api import (load_pycryptodome_raw_lib, c_size_t,
                                  create_string_buffer, get_raw_buffer,
                                  c_uint8_ptr)

_raw_strxor = load_pycryptodome_raw_lib("Crypto.Util._strxor",
                    """
                    void strxor(const uint8_t *in1,
                                const uint8_t *in2,
                                uint8_t *out, size_t len);
                    void strxor_c(const uint8_t *in,
                                  uint8_t c,
                                  uint8_t *out,
                                  size_t len);
                    """)


def strxor(term1, term2):
    """XOR of two byte strings.
    They must have equal length.

    Return:
        A new byte string, :data:`term1` xored with :data:`term2`.
    """

    if len(term1) != len(term2):
        raise ValueError("Only byte strings of equal length can be xored")
    
    result = create_string_buffer(len(term1))
    _raw_strxor.strxor(c_uint8_ptr(term1),
                       c_uint8_ptr(term2),
                       result,
                       c_size_t(len(term1)))
    return get_raw_buffer(result)


def strxor_c(term, c):
    """XOR of a byte string with a repeated sequence of characters.

    Return:
        A new byte string, :data:`term` with all its bytes xored with :data:`c`.
    """

    if not 0 <= c < 256:
        raise ValueError("c must be in range(256)")
    result = create_string_buffer(len(term))
    _raw_strxor.strxor_c(c_uint8_ptr(term), c, result, c_size_t(len(term)))
    return get_raw_buffer(result)

def _strxor_direct(term1, term2, result):
    """Very fast XOR - check conditions!"""
    _raw_strxor.strxor(term1, term2, result, c_size_t(len(term1)))

