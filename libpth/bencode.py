# -*- coding: utf-8 -*-
# pylint: disable=
""" Bencode support.

    Copyright (c) 2009, 2011 The PyroScope Project <pyroscope.project@gmail.com>

    See http://en.wikipedia.org/wiki/Bencode
"""
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

class BencodeError(ValueError):
    """ Error during decoding or encoding.
    """


class Decoder(object):
    """ Decode a string or stream to an object.
    """

    def __init__(self, bytes, char_encoding=None):
        """ Initialize encoder.
        """
        self.bytes = bytes
        self.offset = 0
        self.char_encoding = char_encoding


    def decode(self, check_trailer=False): # pylint: disable=I0011,R0912
        """ Decode data in C{bytes} and return deserialized object.

            @param check_trailer: Raise error if trailing junk is found in data?
            @raise BencodeError: Invalid data.
        """
        try:
            kind = self.bytes[self.offset]
        except IndexError:
            raise BencodeError("Unexpected end of data at offset %d/%d" % (
                self.offset, len(self.bytes),
            ))

        if kind.isdigit():
            # String
            try:
                end = self.bytes.find(':', self.offset)
                length = int(self.bytes[self.offset:end], 10)
            except (ValueError, TypeError):
                raise BencodeError("Bad string length at offset %d (%r...)" % (
                    self.offset, self.bytes[self.offset:self.offset+32]
                ))

            self.offset = end+length+1
            obj = self.bytes[end+1:self.offset]

            if self.char_encoding:
                try:
                    obj = obj.decode(self.char_encoding)
                except UnicodeError:
                    # deliver non-decodable string (bytes arrays) as-is
                    pass
        elif kind == 'i':
            # Integer
            try:
                end = self.bytes.find('e', self.offset+1)
                obj = int(self.bytes[self.offset+1:end], 10)
            except (ValueError, TypeError):
                raise BencodeError("Bad integer at offset %d (%r...)" % (
                    self.offset, self.bytes[self.offset:self.offset+32]
                ))
            self.offset = end+1
        elif kind == 'l':
            # List
            self.offset += 1
            obj = []
            while self.bytes[self.offset:self.offset+1] != 'e':
                obj.append(self.decode())
            self.offset += 1
        elif kind == 'd':
            # Dict
            self.offset += 1
            obj = {}
            while self.bytes[self.offset:self.offset+1] != 'e':
                key = self.decode()
                obj[key] = self.decode()
            self.offset += 1
        else:
            raise BencodeError("Format error at offset %d (%r...)" % (
                self.offset, self.bytes[self.offset:self.offset+32]
            ))

        if check_trailer and self.offset != len(self.bytes):
            raise BencodeError("Trailing data at offset %d (%r...)" % (
                self.offset, self.bytes[self.offset:self.offset+32]
            ))

        return obj


class Encoder(object):
    """ Encode a given object to a string or stream.
    """

    def __init__(self):
        """ Initialize encoder.
        """
        self.result = []


    def encode(self, obj):
        """ Add the given object to the result.
        """
        if isinstance(obj, (int, bool)):
            self.result.append(b"i%de" % obj)
        elif isinstance(obj, str):
            obj = obj.encode('utf8')
            self.result.extend([str(len(obj)).encode('utf8'), b':', obj])
        elif isinstance(obj, bytes):
            self.result.extend([str(len(obj)).encode('utf8'), b':', obj])
        elif hasattr(obj, "__bencode__"):
            self.encode(obj.__bencode__())
        elif isinstance(obj, dict):
            # Dictionary
            self.result.append(b'd')
            for key, val in sorted(obj.items()):
                if not isinstance(key, bytes):
                    key = key.encode('utf8')
                self.result.extend([str(len(key)).encode('utf8'), b':', key])
                self.encode(val)
            self.result.append(b'e')
        else:
            # Treat as iterable
            try:
                items = iter(obj)
            except TypeError as exc:
                raise BencodeError("Unsupported non-iterable object %r of type %s (%s)" % (
                    obj, type(obj), exc
                ))
            else:
                self.result.append(b'l')
                for item in items:
                    self.encode(item)
                self.result.append(b'e')

        return self.result


def bdecode(bytes, char_encoding=None):
    """ Decode a string or stream to an object.
    """
    return Decoder(bytes, char_encoding).decode(check_trailer=True)


def bencode(obj):
    """ Encode a given object to a string.
    """
    return b''.join(Encoder().encode(obj))


def bread(stream):
    """ Decode a file or stream to an object.
    """
    if hasattr(stream, "read"):
        return bdecode(stream.read())
    else:
        handle = open(stream, "rb")
        try:
            return bdecode(handle.read())
        finally:
            handle.close()


def bwrite(stream, obj):
    """ Encode a given object to a file or stream.
    """
    handle = None
    if not hasattr(stream, "write"):
        stream = handle = open(stream, "wb")
    try:
        stream.write(bencode(obj))
    finally:
        if handle:
            handle.close()
