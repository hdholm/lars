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

import sys
import os
import shutil
from datetime import datetime, date, time
from ipaddress import ip_address, IPv4Address, IPv6Address

import pytest

from www2csv import datatypes, geoip
from tests.test_geoip import (
    geolite_country_ipv4_file,
    geolite_country_ipv6_file,
    geolite_city_ipv4_file,
    geolite_city_ipv6_file,
    )


slow = pytest.mark.slow

INTRANET_EXAMPLE = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Date: 2002-05-02 17:42:15
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status cs(User-Agent)
2002-05-02 17:42:15 172.22.255.255 - 172.30.255.255 80 GET /images/picture.jpg - 200 Mozilla/4.0+(compatible;MSIE+5.5;+Windows+2000+Server)
"""

INTERNET_EXAMPLE = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Date: 2002-05-24 20:18:01
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

FTP_EXAMPLE = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Date: 2002-06-04 16:40:23
#Fields: time c-ip cs-method cs-uri-stem sc-status 
16:40:23 10.152.10.200 [6994]USER anonymous 331
16:40:25 10.152.10.200 [6994]PASS anonymous@example.net 530
"""


def test_url():
    assert datatypes.url('foo') == datatypes.Url('', '', 'foo', '', '', '')
    assert datatypes.url('//foo/bar') == datatypes.Url('', 'foo', '/bar', '', '', '')
    assert datatypes.url('http://foo/') == datatypes.Url('http', 'foo', '/', '', '', '')
    assert datatypes.url('http://foo/bar?baz=quux') == datatypes.Url('http', 'foo', '/bar', '', 'baz=quux', '')
    assert datatypes.url('https://foo/bar#baz') == datatypes.Url('https', 'foo', '/bar', '', '', 'baz')

def test_datetime():
    assert datatypes.datetime('2000-01-01 12:34:56') == datetime(2000, 1, 1, 12, 34, 56)
    assert datatypes.datetime('1986-02-28 00:00:00') == datetime(1986, 2, 28)
    with pytest.raises(ValueError):
        datatypes.datetime('2000-01-32 12:34:56')
    with pytest.raises(ValueError):
        datatypes.datetime('2000-01-30 12:34:56 PM')
    with pytest.raises(ValueError):
        datatypes.datetime('foo')

def test_date():
    assert datatypes.date('2000-01-01') == date(2000, 1, 1)
    assert datatypes.date('1986-02-28') == date(1986, 2, 28)
    with pytest.raises(ValueError):
        datatypes.date('1 Jan 2001')
    with pytest.raises(ValueError):
        datatypes.date('2000-01-32')
    with pytest.raises(ValueError):
        datatypes.date('abc')

def test_time():
    assert datatypes.time('12:34:56') == time(12, 34, 56)
    assert datatypes.time('00:00:00') == time(0, 0, 0)
    with pytest.raises(ValueError):
        datatypes.time('1:30:00 PM')
    with pytest.raises(ValueError):
        datatypes.time('25:00:30')
    with pytest.raises(ValueError):
        datatypes.time('abc')

def test_filename(tmpdir):
    assert datatypes.filename('/') == '/'
    assert datatypes.filename('/bin') == '/bin'
    assert datatypes.filename('bin') == 'bin'
    assert datatypes.filename('bin').abspath == os.path.join(os.getcwd(), 'bin')
    assert datatypes.filename('/foo/bar').basename == 'bar'
    assert datatypes.filename('/foo/bar').dirname == '/foo'
    assert datatypes.filename(tmpdir).exists
    assert datatypes.filename(tmpdir).atime == datetime.utcfromtimestamp(tmpdir.stat().atime)
    assert datatypes.filename(tmpdir).mtime == datetime.utcfromtimestamp(tmpdir.stat().mtime)
    assert datatypes.filename(tmpdir).ctime == datetime.utcfromtimestamp(tmpdir.stat().ctime)
    assert datatypes.filename(tmpdir).size == tmpdir.stat().size
    assert datatypes.filename('/foo/bar').isabs
    assert not datatypes.filename('foo/bar').isabs
    assert not datatypes.filename(tmpdir).isfile
    assert not datatypes.filename(tmpdir).islink
    assert datatypes.filename(tmpdir).isdir
    assert datatypes.filename(tmpdir).realpath == tmpdir.realpath()
    assert datatypes.filename('foo/bar').abspath.relative(os.getcwd()) == 'foo/bar'
    # As we're in a temp directory, it can't be a mount
    assert not datatypes.filename('.').ismount
    with pytest.raises(ValueError):
        datatypes.filename('<foo>')
    with pytest.raises(ValueError):
        datatypes.filename('foo*')
    if sys.platform.startswith('win'):
        assert datatypes.filename('/FOO/BAR').normcase == '/foo/bar'
    else:
        assert datatypes.filename('/FOO/BAR').normcase == '/FOO/BAR'
        assert datatypes.filename('/FOO//.//BAR').normpath == '/FOO/BAR'
        tmpdir.join('foo').mksymlinkto(tmpdir)
        tmpdir.join('bar').mksymlinkto(tmpdir.join('foo'))
        tmpdir.join('foo').remove()
        assert not datatypes.filename(tmpdir.join('bar')).exists
        assert datatypes.filename(tmpdir.join('bar')).lexists

def test_hostname():
    assert datatypes.hostname('foo') == datatypes.Hostname('foo')
    assert datatypes.hostname('foo.bar') == datatypes.Hostname('foo.bar')
    assert datatypes.hostname('localhost') == datatypes.Hostname('localhost')
    assert datatypes.hostname('f'*63 + '.o') == datatypes.Hostname('f'*63 + '.o')
    assert datatypes.hostname('f'*63 + '.oo') == datatypes.Hostname('f'*63 + '.oo')
    assert datatypes.hostname('localhost').address == datatypes.address('127.0.0.1')
    assert datatypes.hostname('test.invalid').address is None
    with pytest.raises(ValueError):
        datatypes.hostname('foo.')
    with pytest.raises(ValueError):
        datatypes.hostname('.foo.')
    with pytest.raises(ValueError):
        datatypes.hostname('-foo.bar')
    with pytest.raises(ValueError):
        datatypes.hostname('foo.bar-')
    with pytest.raises(ValueError):
        datatypes.hostname('foo.bar-')
    with pytest.raises(ValueError):
        datatypes.hostname('f'*64 + '.o')
    with pytest.raises(ValueError):
        datatypes.hostname('foo.bar.'*32 + '.com')

def test_address():
    assert datatypes.address('127.0.0.1') == datatypes.IPv4Address('127.0.0.1')
    assert datatypes.address('127.0.0.1:80') == datatypes.IPv4Port('127.0.0.1:80')
    assert datatypes.address('::1') == datatypes.IPv6Address('::1')
    assert datatypes.address('[::1]') == datatypes.IPv6Port('::1')
    assert datatypes.address('[::1]:80') == datatypes.IPv6Port('[::1]:80')
    assert datatypes.address('2001:0db8:85a3:0000:0000:8a2e:0370:7334') == datatypes.IPv6Address('2001:db8:85a3::8a2e:370:7334')
    assert datatypes.address('[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:22') == datatypes.IPv6Port('[2001:db8:85a3::8a2e:370:7334]:22')
    assert datatypes.address('[fe80::7334]:22') == datatypes.IPv6Port('[fe80::7334]:22')
    assert datatypes.address('127.0.0.1').hostname == datatypes.hostname('localhost')
    assert datatypes.address('::1').hostname == datatypes.hostname('ip6-localhost')
    with pytest.raises(ValueError):
        datatypes.address('abc')
    with pytest.raises(ValueError):
        datatypes.address('google.com')
    with pytest.raises(ValueError):
        datatypes.address('127.0.0.1:100000')
    with pytest.raises(ValueError):
        datatypes.address('[::1]:100000')

@slow
def test_address_slow():
    assert datatypes.address('0.0.0.0').hostname is None
    assert datatypes.address('::').hostname is None

def test_address_geoip_countries(
        geolite_country_ipv4_file, geolite_country_ipv6_file):
    geoip.init_database(geolite_country_ipv4_file, geolite_country_ipv6_file)
    assert datatypes.address('127.0.0.1').country is None
    assert datatypes.address('::1').country is None
    assert datatypes.address('80.0.0.0').country == 'GB'
    assert datatypes.address('9.0.0.0').country == 'US'

def test_address_geoip_cities(
        geolite_city_ipv4_file, geolite_city_ipv6_file):
    geoip.init_database(geolite_city_ipv4_file, geolite_city_ipv6_file)
    assert datatypes.address('127.0.0.1').region is None
    assert datatypes.address('80.0.0.0').region == 'D9'
    assert datatypes.address('9.0.0.0').region == 'NC'
    assert datatypes.address('127.0.0.1').city is None
    assert datatypes.address('80.0.0.0').city == 'Greenford'
    assert datatypes.address('9.0.0.0').city == 'Durham'
    assert datatypes.address('127.0.0.1').coords is None
    assert datatypes.address('80.0.0.0').coords == geoip.GeoCoord(-0.33330000000000837, 51.516699999999986)
    assert datatypes.address('9.0.0.0').coords == geoip.GeoCoord(-78.8986, 35.994)

def test_resolving():
    assert datatypes.hostname('localhost').address == datatypes.IPv4Address('127.0.0.1')
    assert datatypes.hostname('localhost') == datatypes.hostname('localhost').address.hostname