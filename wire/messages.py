"""
Messages:

https://wiki.theory.org/BitTorrentSpecification#Messages
<length prefix><message ID><payload>
"""


from collections import namedtuple
from struct import pack
from struct import unpack


FORMAT = '>IB{}'
Message = namedtuple('Message', 'len id payload')

KEEP_ALIVE = -1
CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7
CANCEL = 8
PORT = 9

FORMAT_KEEP_ALIVE = \
FORMAT_CHOKE = \
FORMAT_UNCHOKE = \
FORMAT_INTERESTED = \
FORMAT_NOT_INTERESTED = '>IB'
FORMAT_HAVE = '>IBI'
FORMAT_BITFIELD = '>IB{}B'
FORMAT_REQUEST = '>IBIII'
FORMAT_PIECE = '>IBII{}c'
FORMAT_CANCEL = '>IBIII'
FORMAT_PORT = '>IBH'


def decode(message):
    if len(message) == 4:
        return Message(0, KEEP_ALIVE, None)
    len_, id_ = unpack('>IB', message[:5])
    return [
        decode_choke,
        decode_unchoke,
        decode_interested,
        decode_not_interested,
        decode_have,
        decode_bitfield,
        decode_request,
        decode_piece,
        decode_cancel,
        decode_port,
    ][id_](message, len_ - 1)


# Messages

def keep_alive():
    return b'\x00\x00\x00\x00'


def choke():
    return b'\x00\x00\x00\x01\x00'


def unchoke():
    return b'\x00\x00\x00\x01\x01'


def interested():
    return b'\x00\x00\x00\x01\x02'


def not_interested():
    return b'\x00\x00\x00\x01\x03'


def have(piece_index):
    return pack(FORMAT_HAVE, 5, 4, piece_index)


def bitfield(bits):
    len_ = 1 + len(bits)
    return pack(FORMAT_BITFIELD.format(len_), len_, 5, bits)


def request(index, begin, length):
    return pack(FORMAT_REQUEST, 13, 6, index, begin, length)


def piece(index, begin, block):
    len_ = 9 + len(block)
    return pack(FORMAT_PIECE.format(len_), len_, 7, index, begin, block)


def cancel(index, begin, length):
    return pack(FORMAT_CANCEL, 13, 8, index, begin, length)


def port(listen_port):
    return pack(FORMAT_PORT, 3, 9, listen_port)


# Decoders

def decode_choke(message, _paylen):
    return Message(*unpack(FORMAT_CHOKE, message), None)


def decode_unchoke(message, _paylen):
    return Message(*unpack(FORMAT_UNCHOKE, message), None)


def decode_interested(message, _paylen):
    return Message(*unpack(FORMAT_INTERESTED, message), None)


def decode_not_interested(message, _paylen):
    return Message(*unpack(FORMAT_NOT_INTERESTED, message), None)


def decode_have(message, _paylen):
    return Message(*unpack(FORMAT_HAVE, message))


def decode_bitfield(message, paylen):
    len_, id_, *payload = unpack(FORMAT_BITFIELD.format(paylen), message)
    return Message(len_, id_, payload)


def decode_request(message):
    pass


def decode_piece(message, paylen):
    len_, id_, index, begin, *block = unpack(
        FORMAT_PIECE.format(paylen - 8),
        message
    )
    return Message(len_, id_, (index, begin, block))


def decode_cancel(message):
    pass


def decode_port(message):
    pass
