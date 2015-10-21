#!/usr/bin/env python

from __future__ import print_function, division
import argparse
from . import __version__


def parse_args():
    parser = argparse.ArgumentParser(
        description='2ping (%s)' % __version__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--version', '-V', action='version',
        version=__version__,
        help='report the program version',
    )

    # Positionals
    parser.add_argument(
        'host', type=str, default=None, nargs='?',
        help='host to ping',
    )

    # ping-compatible options
    parser.add_argument(
        '--audible', '-a', dest='audible', action='store_true',
        help='audible ping',
    )
    parser.add_argument(
        '--adaptive', '-A', dest='adaptive', action='store_true',
        help='adaptive RTT ping',
    )
    parser.add_argument(
        '--count', '-c', dest='count', type=int,
        help='number of pings to send',
    )
    parser.add_argument(
        '--flood', '-f', dest='flood', action='store_true',
        help='flood mode',
    )
    parser.add_argument(
        '--interval', '-i', dest='interval', type=float, default=1.0,
        help='seconds between pings', metavar='SECONDS',
    )
    parser.add_argument(
        '--interface-address', '-I', dest='interface_address', type=str, action='append',
        help='interface bind address', metavar='ADDRESS',
    )
    parser.add_argument(
        '--preload', '-l', dest='preload', type=int, default=1,
        help='number of pings to send at start', metavar='COUNT',
    )
    parser.add_argument(
        '--pattern', '-p', dest='pattern', type=str,
        help='hex pattern for padding', metavar='HEX_BYTES',
    )
    parser.add_argument(
        '--quiet', '-q', dest='quiet', action='store_true',
        help='quiet mode',
    )
    parser.add_argument(
        '--packetsize-compat', '-s', dest='packetsize_compat', type=int,
        help='packet size (ping compatible)', metavar='BYTES',
    )
    parser.add_argument(
        '--verbose', '-v', dest='verbose', action='store_true',
        help='verbose mode',
    )
    parser.add_argument(
        '--deadline', '-w', dest='deadline', type=float,
        help='maximum run time', metavar='SECONDS',
    )

    # 2ping options
    parser.add_argument(
        '--auth', type=str,
        help='HMAC authentication key', metavar='KEY',
    )
    parser.add_argument(
        '--auth-digest', type=str, default='hmac-md5',
        choices=['hmac-md5', 'hmac-sha1', 'hmac-sha256', 'hmac-crc32'],
        help='HMAC authentication digest', metavar='DIGEST',
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='debug mode',
    )
    parser.add_argument(
        '--inquire-wait', type=float, default=10.0,
        help='maximum time before loss inquiries', metavar='SECONDS',
    )
    parser.add_argument(
        '--ipv4', '-4', action='store_true',
        help='force IPv4',
    )
    parser.add_argument(
        '--ipv6', '-6', action='store_true',
        help='force IPv6',
    )
    parser.add_argument(
        '--listen', action='store_true',
        help='listen mode',
    )
    parser.add_argument(
        '--max-packet-size', type=int, default=512,
        help='maximum packet size', metavar='BYTES',
    )
    parser.add_argument(
        '--min-packet-size', type=int, default=128,
        help='minimum packet size', metavar='BYTES',
    )
    parser.add_argument(
        '--no-3way', action='store_true',
        help='do not send 3-way pings',
    )
    parser.add_argument(
        '--no-match-packet-size', action='store_true',
        help='do not match packet size of peer',
    )
    parser.add_argument(
        '--no-send-version', action='store_true',
        help='do not send program version to peers',
    )
    parser.add_argument(
        '--notice', type=str,
        help='arbitrary notice text', metavar='TEXT',
    )
    parser.add_argument(
        '--packet-loss', type=str,
        help='percentage simulated packet loss', metavar='OUT:IN',
    )
    parser.add_argument(
        '--port', type=int, default=15998,
        help='port to connect / bind to',
    )
    parser.add_argument(
        '--stats', type=float,
        help='print recurring statistics', metavar='SECONDS',
    )

    # ping-compatible ignored options
    for opt in 'b|B|d|L|n|R|r|U'.split('|'):
        parser.add_argument(
            '-%s' % opt, action='store_true',
            dest='ignored_%s' % opt,
            help=argparse.SUPPRESS,
        )
    for opt in 'F|Q|S|t|T|M|W'.split('|'):
        parser.add_argument(
            '-%s' % opt, type=str, default=None,
            dest='ignored_%s' % opt,
            help=argparse.SUPPRESS,
        )

    args = parser.parse_args()

    if (not args.listen) and (not args.host):
        parser.print_help()
        parser.exit()
    if args.packetsize_compat:
        args.min_packet_size = args.packetsize_compat + 8
    if args.max_packet_size < args.min_packet_size:
        parser.error('Maximum packet size must be at least minimum packet size')
    if args.max_packet_size < 64:
        parser.error('Maximum packet size must be at least 64')
    args.packet_loss_in = 0
    args.packet_loss_out = 0
    if args.packet_loss:
        if ':' in args.packet_loss:
            (v_out, v_in) = args.packet_loss.split(':', 1)
            try:
                args.packet_loss_out = float(v_out)
                args.packet_loss_in = float(v_in)
            except ValueError as e:
                parser.error(e.message)
        else:
            try:
                args.packet_loss_in = args.packet_loss_out = float(args.packet_loss)
            except ValueError as e:
                parser.error('Packet loss: %s' % e.message)
    if args.pattern:
        if len(args.pattern) & 1:
            parser.error('Pattern must be full bytes')
        if len(args.pattern) > 32:
            parser.error('Pattern must be 16 bytes or less')
        args.pattern_bytearray = bytearray()
        for i in xrange(int(len(args.pattern) / 2)):
            a = args.pattern[(i*2):(i*2+2)]
            try:
                b = int(a, 16)
            except ValueError as e:
                parser.error('Pattern: %s' % e.message)
            args.pattern_bytearray += bytearray([b])
    else:
        args.pattern_bytearray = bytearray(1)

    hmac_id_map = {
        'hmac-md5': 1,
        'hmac-sha1': 2,
        'hmac-sha256': 3,
        'hmac-crc32': 4,
    }
    args.auth_digest_index = hmac_id_map[args.auth_digest]

    if args.debug:
        args.verbose = True

    return args