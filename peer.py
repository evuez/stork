"""
Generate a peer id using Shadow's style peer id:
http://forums.degreez.net/viewtopic.php?t=7070.
"""

from random import shuffle


B64_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.-'


def _header(identifier, version):
    identifier = identifier.upper()
    version = "{:x}{:x}{:x}".format(*map(int, version.split('.'))).upper()
    return (identifier + version).ljust(6, '-')


def _body():
    chars = list(B64_CHARS)
    shuffle(chars)
    return '---' + ''.join(chars[:11])


def peer_id(identifier, version):
    return _header(identifier, version) + _body()


def peers_from_list(peer_list):
    return [Peer(p[b'peer id'], p[b'ip'], p[b'port']) for p in peer_list]


class Peer(object):
    def __init__(self, id_, ip, port):
        self.id = id_
        self.ip = ip
        self.port = port
        self.bitfield = None

    def __str__(self):
        return "Peer<{}:{}>".format(self.ip.decode(), self.port)

    def update_bitfield(self, have_message):
        pass
