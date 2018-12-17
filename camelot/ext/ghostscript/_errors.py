"""
Definition of Ghostscript error codes
"""
#
# Copyright (C) 2010-2018 by Hartmut Goebel
#
# Based on iapi.h which is
# Copyright (C) 1989, 1995, 1998, 1999 Aladdin Enterprises. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

__author__ = "Hartmut Goebel <h.goebel@crazy-compilers.com>"
__copyright__ = "Copyright 2010-2018 by Hartmut Goebel <h.goebel@crazy-compilers.com>"
__licence__ = "GNU General Public License version 3 (GPL v3)"
__version__ = "0.6"


LEVEL1_ERROR_NAMES = ["unknownerror", "dictfull", "dictstackoverflow",
                      "dictstackunderflow", "execstackoverflow",
                      "interrupt", "invalidaccess", "invalidexit",
                      "invalidfileaccess", "invalidfont",
                      "invalidrestore", "ioerror", "limitcheck",
                      "nocurrentpoint", "rangecheck", "stackoverflow",
                      "stackunderflow", "syntaxerror", "timeout",
                      "typecheck", "undefined", "undefinedfilename",
                      "undefinedresult", "unmatchedmark", "VMerror"]

LEVEL2_ERROR_NAMES = ["configurationerror", "invalidcontext",
                      "undefinedresource", "unregistered",
                      "invalidid"]

ERROR_NAMES = LEVEL1_ERROR_NAMES + LEVEL2_ERROR_NAMES

PSEUDO_ERROR_NAMES = ['Fatal', 'Quit', 'InterpreterExit', 'RemapColor',
                      'ExecStackUnderflow', 'VMreclaim', 'NeedInput',
                      'NeedStdin', 'NeedStdout', 'NeedStderr', 'Info']


def error2name(ecode):
    if ecode <= e_Fatal:
        return PSEUDO_ERROR_NAMES[-ecode-100]
    else:
        return ERROR_NAMES[-ecode-1]


#
# Internal code for a fatal error.
# gs_interpret also returns this for a .quit with a positive exit code.
#
e_Fatal = -100

#
# Internal code for the .quit operator.
# The real quit code is an integer on the operand stack.
# gs_interpret returns this only for a .quit with a zero exit code.
#
e_Quit = -101

#
# Internal code for a normal exit from the interpreter.
# Do not use outside of interp.c.
#
e_InterpreterExit = -102

#
# Internal code that indicates that a procedure has been stored in the
# remap_proc of the graphics state, and should be called before retrying
# the current token. This is used for color remapping involving a call
# back into the interpreter -- inelegant, but effective.
#
e_RemapColor = -103

#
# Internal code to indicate we have underflowed the top block
# of the e-stack.
#
e_ExecStackUnderflow = -104

#
# Internal code for the vmreclaim operator with a positive operand.
# We need to handle this as an error because otherwise the interpreter
# won't reload enough of its state when the operator returns.
#
e_VMreclaim = -105

#
# Internal code for requesting more input from run_string.
#
e_NeedInput = -106

#
# Internal code for stdin callout.
#
e_NeedStdin = -107

#
# Internal code for stdout callout.
#
e_NeedStdout = -108

#
# Internal code for stderr callout.
#
e_NeedStderr = -109

#
# Internal code for a normal exit when usage info is displayed.
# This allows Window versions of Ghostscript to pause until
# the message can be read.
#
e_Info = -110
