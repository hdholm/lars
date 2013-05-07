# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright (c) 2013 Dave Hughes
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
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import pytest

from www2csv import dns


slow = pytest.mark.slow


def test_from_address():
    assert dns.from_address('127.0.0.1') == 'localhost'
    # XXX Not sure this is going to be true on all platforms...
    assert dns.from_address('::1') == 'ip6-localhost'

@slow
def test_from_address_slow():
    assert dns.from_address('9.0.0.0') == '9.0.0.0'
    assert dns.from_address('0.0.0.0') == '0.0.0.0'

def test_to_address():
    assert dns.to_address('localhost') == '127.0.0.1'
    assert dns.to_address('ip6-localhost') == '::1'
    assert dns.to_address('foo.bar') is None
    assert dns.to_address('0.0.0.0') == '0.0.0.0'
    assert dns.to_address('9.0.0.0') == '9.0.0.0'