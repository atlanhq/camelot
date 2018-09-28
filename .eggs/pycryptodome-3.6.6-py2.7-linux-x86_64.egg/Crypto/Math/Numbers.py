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

"""Fast, arbitrary precision integers.

:undocumented: __package__
"""

__all__ = ["Integer"]

from Crypto.Util.py3compat import *
from Crypto import Random

try:
    from Crypto.Math._Numbers_gmp import Integer
    from Crypto.Math._Numbers_gmp import implementation as _implementation
except (ImportError, OSError, AttributeError):
    try:
        from Crypto.Math._Numbers_custom import Integer
        from Crypto.Math._Numbers_custom import implementation as _implementation
    except (ImportError, OSError):
        from Crypto.Math._Numbers_int import Integer
        _implementation = { }


def _random(**kwargs):
    """Generate a random natural integer of a certain size.

    :Keywords:
      exact_bits : positive integer
        The length in bits of the resulting random Integer number.
        The number is guaranteed to fulfil the relation:

            2^bits > result >= 2^(bits - 1)

      max_bits : positive integer
        The maximum length in bits of the resulting random Integer number.
        The number is guaranteed to fulfil the relation:

            2^bits > result >=0

      randfunc : callable
        A function that returns a random byte string. The length of the
        byte string is passed as parameter. Optional.
        If not provided (or ``None``), randomness is read from the system RNG.

    :Return: a Integer object
    """

    exact_bits = kwargs.pop("exact_bits", None)
    max_bits = kwargs.pop("max_bits", None)
    randfunc = kwargs.pop("randfunc", None)

    if randfunc is None:
        randfunc = Random.new().read

    if exact_bits is None and max_bits is None:
        raise ValueError("Either 'exact_bits' or 'max_bits' must be specified")

    if exact_bits is not None and max_bits is not None:
        raise ValueError("'exact_bits' and 'max_bits' are mutually exclusive")

    bits = exact_bits or max_bits
    bytes_needed = ((bits - 1) // 8) + 1
    significant_bits_msb = 8 - (bytes_needed * 8 - bits)
    msb = bord(randfunc(1)[0])
    if exact_bits is not None:
        msb |= 1 << (significant_bits_msb - 1)
    msb &= (1 << significant_bits_msb) - 1

    return Integer.from_bytes(bchr(msb) + randfunc(bytes_needed - 1))


def _random_range(**kwargs):
    """Generate a random integer within a given internal.

    :Keywords:
      min_inclusive : integer
        The lower end of the interval (inclusive).
      max_inclusive : integer
        The higher end of the interval (inclusive).
      max_exclusive : integer
        The higher end of the interval (exclusive).
      randfunc : callable
        A function that returns a random byte string. The length of the
        byte string is passed as parameter. Optional.
        If not provided (or ``None``), randomness is read from the system RNG.
    :Returns:
        An Integer randomly taken in the given interval.
    """

    min_inclusive = kwargs.pop("min_inclusive", None)
    max_inclusive = kwargs.pop("max_inclusive", None)
    max_exclusive = kwargs.pop("max_exclusive", None)
    randfunc = kwargs.pop("randfunc", None)

    if kwargs:
        raise ValueError("Unknown keywords: " + str(kwargs.keys))
    if None not in (max_inclusive, max_exclusive):
        raise ValueError("max_inclusive and max_exclusive cannot be both"
                         " specified")
    if max_exclusive is not None:
        max_inclusive = max_exclusive - 1
    if None in (min_inclusive, max_inclusive):
        raise ValueError("Missing keyword to identify the interval")

    if randfunc is None:
        randfunc = Random.new().read

    norm_maximum = max_inclusive - min_inclusive
    bits_needed = Integer(norm_maximum).size_in_bits()

    norm_candidate = -1
    while not 0 <= norm_candidate <= norm_maximum:
        norm_candidate = _random(
                                max_bits=bits_needed,
                                randfunc=randfunc
                                )
    return norm_candidate + min_inclusive

Integer.random = staticmethod(_random)
Integer.random_range = staticmethod(_random_range)
