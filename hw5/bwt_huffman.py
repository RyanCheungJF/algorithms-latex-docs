import os
import sys
import marshal
import itertools
import argparse
import pickle
from operator import itemgetter
from functools import partial
from collections import Counter, defaultdict
from heapq import heappush, heappop

# try:
#     import cPickle as pickle
# except:
#     import pickle

termchar = 17  # you can assume the byte 17 does not appear in the input file


# This takes in the bytes and generates the huffman tree, running the greedy algorithm on it.
def construct_huffman_tree(msg: bytes) -> (int, list):
    # gets freq count
    freq = defaultdict(int)
    for b in msg:
        freq[b] += 1

    min_heap = []
    for key, val in freq.items():
        # stores freq, [arr of child nodes] where each node is (key, binary encoding)
        heappush(min_heap, (val, [(key, "")]))

    # we want to greedily combine two of the smallest elems until we get one item left in order to build our tree
    while len(min_heap) > 1:
        l_freq, l_arr = heappop(min_heap)
        r_freq, r_arr = heappop(min_heap)

        # for each child in our subtree, add in either 0 or 1 as we go from bottom to top (leaf to root)
        for i, pair in enumerate(l_arr):
            key, binary = pair
            l_arr[i] = (key, "0" + binary)
        for i, pair in enumerate(r_arr):
            key, binary = pair
            r_arr[i] = (key, "1" + binary)

        # combine to form new tree
        subtree = (l_freq + r_freq, l_arr + r_arr)
        heappush(min_heap, subtree)

    return min_heap[0]


# This takes the output of the huffman tree, and forms a mapping.
def construct_huffman_encoder(msg: bytes) -> dict:
    _, encoding = construct_huffman_tree(msg)
    mapping = {}
    for c, enc in encoding:
        # need to keep a forward and reverse mapping for encoding, decoding respectively
        mapping[enc] = c
        mapping[c] = enc
    return mapping


# This uses the mapping provided to encode the original message to an ASCII representation.
def encode_message_with_huffman(msg: bytes, ring: dict) -> str:
    string_builder = []
    for c in msg:
        string_builder.append(ring[c])
    return "".join(string_builder)


# This takes a sequence of bytes over which you can iterate, msg,
# and returns a tuple (enc, ring) in which enc is the ASCII representation of the
# Huffman-encoded message (e.g. "1001011") and ring is your decoder ring needed
# to decompress that message.
def encode(msg: bytes) -> (str, dict):
    ring = construct_huffman_encoder(msg)
    binary = encode_message_with_huffman(msg, ring)
    return (binary, ring)


# This takes a string, cmsg, which must contain only 0s and 1s, and your
# representation of the decoder ring ring, and returns a bytearray msg which
# is the decompressed message.
def decode(cmsg: str, decoder_ring: dict) -> bytes:
    # creates an array with the appropriate type so that the message can be decoded
    byte_msg = bytearray()
    i = 0
    curr = ""

    while i < len(cmsg):
        while i < len(cmsg) and curr not in decoder_ring:
            curr += cmsg[i]
            i += 1
        byte_msg.append(decoder_ring.get(curr))
        curr = ""

    return byte_msg


# This takes a sequence of bytes over which you can iterate, msg, and returns a tuple (compressed, ring)
# in which compressed is a bytearray (containing the Huffman-coded message in binary,
# and ring is again the decoder ring needed to decompress the message.
def compress(msg: bytes, useBWT: bool) -> (bytes, dict):
    # only do bwt and mtf if file is non binary, as binary files can contain terminating char
    if useBWT:
        msg = bwt(msg)
        msg = mtf(msg)

    # perform huffman encoding, getting back a binary string of the file and the huffman encoding
    binary_string, ring = encode(msg)

    # ince we want to pack it into a bytearray of size 8s, we pad it with 0s and note down the pad
    ring["PADDING"] = 8 - (len(binary_string) % 8)
    binary_string += "0" * (8 - (len(binary_string) % 8))

    # initializes an array to hold the compressed message
    compressed = bytearray()
    # we convert the message into the hex value of a byte
    for i in range(len(binary_string) // 8):
        byteString = binary_string[i * 8 : (i + 1) * 8]
        compressed.append(int(byteString, 2))

    return compressed, ring


# This takes a sequence of bytes over which you can iterate containing the Huffman-coded message, and the
# decoder ring needed to decompress it.  It returns the bytearray which is the decompressed message.
def decompress(msg: bytes, decoder_ring: dict, useBWT: bool) -> bytes:
    # creates an array with the appropriate type so that the message can be decoded
    byte_array = bytearray(msg)

    string_builder = []
    # convert the ASCII value back into 8 bit binary strings
    for ascii_value in byte_array:
        string_builder.append("{0:08b}".format(ascii_value))
    binary_string = "".join(string_builder)
    # remove the padding here to get back the original string
    binary_string = binary_string[: -decoder_ring.get("PADDING", 0)]

    decompressed_msg = decode(binary_string, decoder_ring)

    # before you return, you must invert the move-to-front and BWT if applicable
    # here, decompressed message should be the return value from decode()
    if useBWT:
        decompressed_msg = imtf(decompressed_msg)
        decompressed_msg = ibwt(decompressed_msg)

    return decompressed_msg


# Burrows-Wheeler Transform fncs
def radix_sort(values, key, step=0):
    sortedvals = []
    radix_stack = []
    radix_stack.append((values, key, step))

    while len(radix_stack) > 0:
        values, key, step = radix_stack.pop()
        if len(values) < 2:
            for value in values:
                sortedvals.append(value)
            continue

        bins = {}
        for value in values:
            bins.setdefault(key(value, step), []).append(value)

        for k in sorted(bins.keys()):
            radix_stack.append((bins[k], key, step + 1))
    return sortedvals


# memory efficient iBWT
def ibwt(msg: bytes) -> bytes:
    # creates a map for the original msg of (char, relative order) -> index
    seen = {}
    msg_hm = {}
    for i, b in enumerate(msg):
        freq = seen[b] + 1 if b in seen else 1
        seen[b] = freq
        msg_hm[(b, freq)] = i

    sorted_msg = sorted(msg)

    # creates a map for the sorted msg of index -> (char, relative order)
    seen = {}
    sorted_msg_hm = {}
    for i, b in enumerate(sorted_msg):
        freq = seen[b] + 1 if b in seen else 1
        seen[b] = freq
        sorted_msg_hm[i] = (b, freq)

    bwtM = bytearray()
    # start from the terminating character and use the relative order property
    curr = termchar
    freq = 1
    while len(bwtM) < len(msg):
        # from a char in the msg, finds the char at same index in the sorted msg,
        # then finds that particular char (while preserving relative order) in the msg,
        # and continuously repeat until we get the original string
        idx = msg_hm[(curr, freq)]
        b, f = sorted_msg_hm[idx]
        bwtM.append(b)
        curr, freq = b, f
    bwtM.remove(termchar)

    return bwtM


# memory efficient BWT
def bwt(msg: bytes) -> bytes:
    def bw_key(text, value, step):
        return text[(value + step) % len(text)]

    msg = msg + termchar.to_bytes(1, byteorder="big")
    bwtM = bytearray()

    rs = radix_sort(range(len(msg)), partial(bw_key, msg))
    for i in rs:
        bwtM.append(msg[i - 1])
    return bwtM[::-1]


# move-to-front encoding fncs
def mtf(msg: bytes) -> bytes:
    # Initialise the list of characters (i.e. the dictionary)
    dictionary = bytearray(range(256))

    # transformation
    compressed_text = bytearray()
    rank = 0

    # read in each character
    for c in msg:
        rank = dictionary.index(c)  # find the rank of the character in the dictionary
        compressed_text.append(rank)  # update the encoded text

        # update the dictionary
        dictionary.pop(rank)
        dictionary.insert(0, c)

    # dictionary.sort() # sort dictionary
    return compressed_text  # Return the encoded text as well as the dictionary


# inverse move-to-front
def imtf(compressed_msg: bytes) -> bytes:
    compressed_text = compressed_msg
    dictionary = bytearray(range(256))

    decompressed_img = bytearray()

    # read in each character of the encoded text
    for i in compressed_text:
        # read the rank of the character from dictionary
        decompressed_img.append(dictionary[i])

        # update dictionary
        e = dictionary.pop(i)
        dictionary.insert(0, e)

    return decompressed_img  # Return original string


if __name__ == "__main__":
    # argparse is an excellent library for parsing arguments to a python program
    parser = argparse.ArgumentParser(
        description="<Insert a cool name for your compression algorithm> compresses "
        "binary and plain text files using the Burrows-Wheeler transform, "
        "move-to-front coding, and Huffman coding."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-c",
        action="store_true",
        help="Compresses a stream of bytes (e.g. file) into a bytes.",
    )
    group.add_argument(
        "-d",
        action="store_true",
        help="Decompresses a compressed file back into the original input",
    )
    group.add_argument(
        "-v",
        action="store_true",
        help="Encodes a stream of bytes (e.g. file) into a binary string"
        " using Huffman encoding.",
    )
    group.add_argument(
        "-w",
        action="store_true",
        help="Decodes a Huffman encoded binary string into bytes.",
    )
    parser.add_argument("-i", "--input", help="Input file path", required=True)
    parser.add_argument("-o", "--output", help="Output file path", required=True)
    parser.add_argument(
        "-b",
        "--binary",
        help="Use this option if the file is binary and therefore "
        "do not want to use the BWT.",
        action="store_true",
    )

    args = parser.parse_args()

    compressing = args.c
    decompressing = args.d
    encoding = args.v
    decoding = args.w

    infile = args.input
    outfile = args.output
    # if a binary file, useBWT is false
    useBWT = not args.binary

    assert os.path.exists(infile)

    if compressing or encoding:
        fp = open(infile, "rb")
        sinput = fp.read()
        fp.close()
        if compressing:
            msg, tree = compress(sinput, useBWT)
            fcompressed = open(outfile, "wb")
            marshal.dump((pickle.dumps(tree), msg), fcompressed)
            fcompressed.close()
        else:
            msg, tree = encode(sinput)
            fcompressed = open(outfile, "wb")
            marshal.dump((pickle.dumps(tree), msg), fcompressed)
            fcompressed.close()
    else:
        fp = open(infile, "rb")
        pck, msg = marshal.load(fp)
        tree = pickle.loads(pck)
        fp.close()
        if decompressing:
            sinput = decompress(msg, tree, useBWT)
        else:
            sinput = decode(msg, tree)
        fp = open(outfile, "wb")
        fp.write(sinput)
        fp.close()
