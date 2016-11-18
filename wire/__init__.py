from struct import unpack


def get_message_length(bytes_):
    return unpack('>I', bytes_[:4])[0]
