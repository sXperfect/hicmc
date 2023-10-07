##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @file Description
# @copyright Institute fuer Informationsverarbeitung

import bitstream
import numpy
from bitstream import BitStream
from numpy.typing import NDArray
import math
from . import transform

class uint(object):
    def __init__(self, bits):
        self._bits = bits


def encode_uint_factory(instance):
    _bits = instance._bits

    def write_uint(stream, data):
        if isinstance(data, list) or isinstance(data, numpy.ndarray):
            for integer in data:
                write_uint(stream, integer)

        else:
            integer = int(data)
            if integer < 0:
                raise ValueError(f"Number is negative, Number: {integer}")

            booleans = []
            for _ in range(_bits):
                booleans.append(integer & 1)
                integer = integer >> 1

            booleans.reverse()
            stream.write(booleans, bool)

    return write_uint


def decode_uint_factory(instance):
    _bits = instance._bits

    def read_uint(stream, n=None):
        if n is None:
            integer = 0
            for _ in range(_bits):
                integer = integer << 1
                if stream.read(bool):
                    integer += 1
                    
            return integer

        else:
            return [read_uint(stream) for _ in range(n)]

    return read_uint


bitstream.register(uint, reader=decode_uint_factory, writer=encode_uint_factory)


_padding_bits = 4
_counts_size_bits = 8


def encode_binary_array(array: NDArray[numpy.bool_], _transform: bool) -> bytes:

    _head = BitStream()

    #? Write transform-lag
    _head.write(_transform, bool)
    if _transform:
        
        #? Transform using binary run-length encoding
        val, counts = transform.encode_binary_run_length(array)
        
        counts_size = math.ceil(math.log2(counts.max() + 1))
        
        #? Write first-value
        _head.write(val, bool)

        #? Write integer-size
        _head.write(counts_size, uint(_counts_size_bits))
        
        #? Write data
        _data = BitStream(counts, uint(counts_size))

    else:
        _data = BitStream(array, bool)

    #? Add padding to payload
    padding = (8 - len(_data)) % 8
    _head.write(padding, uint(_padding_bits))
    _data.write([0] * padding, bool)
    
    #? Add padding to header
    _head.write([0] * (8 - len(_head) % 8), bool)
    return _head.read(bytes) + _data.read(bytes)


def decode_binary_array(payload: bytes) -> NDArray[numpy.bool_]:

    _stream = BitStream(payload)
    
    #? Read transform-flag
    _transform = _stream.read(bool)
    if _transform:
        
        #? Read first-value
        first_value = _stream.read(bool)

        #? Read integer-size
        counts_size = _stream.read(uint(_counts_size_bits))
        
        #? Read padding
        padding = _stream.read(uint(_padding_bits))        
        _stream.read(bool, len(_stream) % 8)

        #? Read data
        counts = numpy.array(_stream.read(uint(counts_size), (len(_stream) - padding) // counts_size), dtype=numpy.integer)
        return transform.decode_binary_run_length(first_value, counts)

    else:

        #? Read padding
        padding = _stream.read(uint(_padding_bits))
        _stream.read(bool, len(_stream) % 8)

        #? Read data
        return _stream.read(bool, len(_stream) - padding)
