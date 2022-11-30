# vim: set fileencoding=utf-8 :

# This code is original from jsmin by Douglas Crockford, it was translated to
# Python by Baruch Even. It was rewritten by Dave St.Germain for speed.
#
# The MIT License (MIT)
#
# Copyright (c) 2013 Dave St.Germain
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import io
import string
from typing import Tuple, Optional, TextIO

__all__ = ["jsmin", "JavascriptMinify"]
__version__ = "3.1.0"


def jsmin(js: str, **kwargs):
    """Minify a javascript string"""
    ins = io.StringIO(js)
    outs = io.StringIO()
    JavascriptMinify(ins, outs, **kwargs).minify()
    return outs.getvalue()


class JavascriptMinify(object):
    def __init__(
        self,
        instream: Optional[TextIO] = None,
        outstream: Optional[TextIO] = None,
        quote_chars: str = "'\"",
    ):
        self.ins, self.outs = instream, outstream

        space_chars = string.ascii_letters + string.digits + "_$\\"
        starters = "{[(+-"
        enders = "}])+-/" + quote_chars
        newline_start_chars = starters + space_chars + quote_chars
        newline_end_chars = enders + space_chars + quote_chars

        self.newline_start_chars = newline_start_chars
        self.newline_end_chars = newline_end_chars
        self.quote_chars = quote_chars
        self.space_chars = space_chars

    def minify(
        self,
        instream: Optional[TextIO] = None,
        outstream: Optional[TextIO] = None,
    ):
        """Minify an input stream of javascript, writing to an output stream"""
        if instream and outstream:
            self.ins, self.outs = instream, outstream

        assert self.ins, "No input stream"
        assert self.outs, "No output stream"

        self.is_return = False
        self.return_buf = ""

        def write(char: str) -> None:
            # all of this is to support literal regular expressions.
            # sigh
            if char in "return":
                self.return_buf += char
                self.is_return = self.return_buf == "return"
            else:
                self.return_buf = ""
                self.is_return = self.is_return and char < "!"
            self.outs.write(char)  # type: ignore
            if self.is_return:
                self.return_buf = ""

        read = self.ins.read

        do_newline = False
        do_space = False
        escape_slash_count = 0
        in_quote = ""
        quote_buf = []

        previous = ";"
        previous_non_space = ";"
        next1 = read(1)

        while next1:
            next2 = read(1)
            if in_quote:
                quote_buf.append(next1)

                if next1 == in_quote:
                    numslashes = 0
                    for c in reversed(quote_buf[:-1]):
                        if c != "\\":
                            break
                        else:
                            numslashes += 1
                    if numslashes % 2 == 0:
                        in_quote = ""
                        write("".join(quote_buf))
            elif next1 in "\r\n":
                next2, do_newline = self._newline(previous_non_space, next2, do_newline)
            elif next1 < "!":
                if (
                    previous_non_space in self.space_chars or previous_non_space > "~"
                ) and (next2 in self.space_chars or next2 > "~"):
                    do_space = True
                elif previous_non_space in "-+" and next2 == previous_non_space:
                    # protect against + ++ or - -- sequences
                    do_space = True
                elif self.is_return and next2 == "/":
                    # returning a regex...
                    write(" ")
            elif next1 == "/":
                if do_space:
                    write(" ")
                if next2 == "/":
                    # Line comment: treat it as a newline, but skip it
                    next2 = self._line_comment(next1, next2)
                    next1 = "\n"
                    next2, do_newline = self._newline(
                        previous_non_space, next2, do_newline
                    )
                elif next2 == "*":
                    self._block_comment(next1, next2)
                    next2 = read(1)
                    if previous_non_space in self.space_chars:
                        do_space = True
                    next1 = previous
                else:
                    if previous_non_space in "{(,=:[?!&|;" or self.is_return:
                        self._regex_literal(next1, next2)
                        # hackish: after regex literal next1 is still /
                        # (it was the initial /, now it's the last /)
                        next2 = read(1)
                    else:
                        write("/")
            else:
                if do_newline:
                    write("\n")
                    do_newline = False
                    do_space = False
                if do_space:
                    do_space = False
                    write(" ")

                write(next1)
                if next1 in self.quote_chars:
                    in_quote = next1
                    quote_buf = []

            if next1 >= "!":
                previous_non_space = next1

            if next1 == "\\":
                escape_slash_count += 1
            else:
                escape_slash_count = 0

            previous = next1
            next1 = next2

    def _regex_literal(self, next1: str, next2: str) -> None:
        assert next1 == "/"
        assert self.ins
        assert self.outs

        self.return_buf = ""

        read = self.ins.read
        write = self.outs.write

        in_char_class = False

        write("/")

        _next = next2
        while _next and (_next != "/" or in_char_class):
            write(_next)
            if _next == "\\":
                write(read(1))  # whatever is next is escaped
            elif _next == "[":
                write(read(1))  # character class cannot be empty
                in_char_class = True
            elif _next == "]":
                in_char_class = False
            _next = read(1)

        write("/")

    def _line_comment(self, next1: str, next2: str) -> str:
        assert next1 == next2 == "/"
        assert self.ins, "No input stream"

        read = self.ins.read

        while next1 and next1 not in "\r\n":
            next1 = read(1)
        while next1 and next1 in "\r\n":
            next1 = read(1)

        return next1

    def _block_comment(self, next1: str, next2: str) -> None:
        assert next1 == "/"
        assert next2 == "*"
        assert self.ins, "No input stream"
        assert self.outs, "No output stream"

        read = self.ins.read

        # Skip past first /* and avoid catching on /*/...*/
        next1 = read(1)
        next2 = read(1)

        comment_buffer = "/*"
        while next1 != "*" or next2 != "/":
            comment_buffer += next1
            next1 = next2
            next2 = read(1)

        if comment_buffer.startswith("/*!"):
            # comment needs preserving
            self.outs.write(comment_buffer)
            self.outs.write("*/\n")

    def _newline(
        self, previous_non_space: str, next2: str, do_newline: bool
    ) -> Tuple[str, bool]:
        assert self.ins, "No input stream"
        read = self.ins.read

        if (
            previous_non_space
            and previous_non_space in self.newline_end_chars
            or previous_non_space > "~"
        ):
            while True:
                if next2 < "!":
                    next2 = read(1)
                    if not next2:
                        break
                else:
                    if next2 in self.newline_start_chars or next2 > "~" or next2 == "/":
                        do_newline = True
                    break

        return next2, do_newline
