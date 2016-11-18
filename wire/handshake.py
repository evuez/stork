"""
Handshake:

https://wiki.theory.org/BitTorrentSpecification#Handshake
<pstrlen><pstr><reserved><info_hash><peer_id>
"""


from collections import namedtuple
from struct import pack
from struct import unpack


SIZE = 68
PSTR = b"BitTorrent protocol"
FORMAT = '>{}p8x20s20s'.format(len(PSTR) + 1)
Handshake = namedtuple('Handshake', 'pstr info_hash peer_id')


def encode(info_hash, peer_id):
    return pack(FORMAT, PSTR, info_hash, peer_id)


def decode(handshake):
    return Handshake(*unpack(FORMAT, handshake))
