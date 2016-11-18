from hashlib import sha1
from random import randint
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse
from urllib.request import urlopen
from bencodepy import decode as bdecode
from bencodepy import encode as bencode
from peer import Peer
from peer import peers_from_list
from peer import peer_id


IDENTIFIER = 'P'
VERSION = '0.0.1'

PEER_ID = peer_id(IDENTIFIER, VERSION)
PORT = randint(6881, 6889)


class Torrent(object):
    def __init__(self, torrent_file):
        self._decode(torrent_file)

    def _decode(self, torrent_file):
        with open(torrent_file, 'rb') as f:
            self.torrent = f.read()
        odict = bdecode(self.torrent)

        self.announce = odict[b'announce'].decode('utf-8')
        self.info = odict[b'info']
        self.length = self._length(self.info)
        self.hash = sha1(bencode(self.info)).digest()

    def _length(self, info):
        try: # Single-file mode.
            return info[b'length']
        except KeyError: # Multi-file mode.
            return sum(f[b'length'] for f in info[b'files'])

    @property
    def tracker_request_url(self):
        announce = list(urlparse(self.announce))
        announce[4] = urlencode({
            'info_hash': self.hash,
            'peer_id': PEER_ID,
            'port': PORT,
            'left': self.length,
            'uploaded': 0,
            'downloaded': 0,
        })
        return urlunparse(announce)


class Tracker(object):
    class TrackerError(Exception):
        pass

    def __init__(self, info):
        self.interval = info[b'interval']
        self.tracker_id = info.get('tracker id')
        self.seeders = info.get(b'complete')
        self.leechers = info.get(b'incomplete')
        self.peers = peers_from_list(info[b'peers'])

    @classmethod
    def from_url(cls, request_url):
        return cls(cls.tracker_info(urlopen(request_url).read()))

    @staticmethod
    def tracker_info(response):
        info = bdecode(response)
        failure = info.get(b'failure reason')
        if not failure:
            return info
        raise Tracker.TrackerError(
            "Tracker return with error: {}".format(failure)
        )


### TESTS

torrent = Torrent('torrents/fedora.torrent')
tracker = Tracker.from_url(torrent.tracker_request_url)


import asyncio
from wire import handshake
from wire import messages
from wire import get_message_length


class Client(object):

    def __init__(self, torrent, peer):
        self.torrent = torrent
        self.peer = peer

        self.choked = True
        self.interested = False
        self.peer_choked = True
        self.peer_interested = False

        self.handshake = handshake.encode(self.torrent.hash, PEER_ID.encode())

        self.bitfield = {}  # Downloaded pieces

    def request(self):
        from random import choice
        index, _ = choice([(k,b) for k,b in enumerate(self.peer.bitfield) if b == 255])
        return messages.request(index * 8, 0, 16 * 8)

    def handle_keep_alive(self, peer):
        pass

    def handle_choke(self):
        self.choked = True

    def handle_unchoke(self):
        self.choked = False

    def handle_interested(self):
        self.peer_interested = True

    def handle_not_interested(self):
        self.peer_interested = False

    def handle_have(self, message):
        # should make sure bitfield is at least index // 8 long
        # use self.torrent.length
        index = message.payload
        self.peer.bitfield[index // 8] |= (1 << (7 - index % 8))

    def handle_bitfield(self, message):
        self.peer.bitfield = list(message.payload)

    def handle_request(self):
        pass

    def handle_piece(self, message):
        index, begin, block = message.payload
        self.bitfield[index] = 1
        # write to file

    def handle_cancel(self):
        pass

    def handle_port(self):
        pass

client = Client(torrent, tracker.peers[0])

async def test(loop):
    reader, writer = await asyncio.open_connection(client.peer.ip, client.peer.port, loop=loop)
    writer.write(client.handshake)
    data = await reader.readexactly(handshake.SIZE)
    if handshake.decode(data).peer_id == client.peer.id:
        print('OK')
    else:
        print('KO')
        writer.close()
        return False

    writer.write(messages.interested())
    while True:
        data = await reader.readexactly(4)
        len_ = get_message_length(data)
        data += await reader.readexactly(len_)
        message = messages.decode(data)
        print("Message id:", message.id)
        if message.id == messages.BITFIELD:
            client.handle_bitfield(message)
        elif message.id == messages.HAVE:
            client.handle_have(message)

        if client.peer.bitfield:
            writer.write(client.request())


    writer.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
