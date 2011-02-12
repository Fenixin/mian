#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mian - Mine analysis - Graph block types to altitude in a Minecraft save
game <http://github.com/l0b0/mian>

Default syntax:

mian [-b|--blocks=<list>] [-l|--list] <World directory>

Options:

-b, --blocks    Specify block types to include as a comma-separated list, using
                either the block types or hex values from the list.
-l, --list      List available block types and their names (from
                <http://www.minecraftwiki.net/wiki/Data_values>).
-n, --nether    Graph The Nether instead of the ordinary world.

Description:

Creates a file with a graph of how much the given materials occur at each
vertical layer of the map.

Examples:

$ mian ~/.minecraft/saves/World1
Creates graph of default materials in World1.

$ mian -b 01,dirt,09,sand ~/.minecraft/saves/World1
Ditto, showing only the specified block types.

$ mian -b 56,57,58,59,5a,5b -n ~/.minecraft/saves/World1
Graph all the materials new to The Nether.

$ mian --list
Show a list of block types which can be searched for.
"""

__author__ = 'Pepijn de Vos, Victor Engmark'
__copyright__ = 'Copyright (C) 2010-2011 Pepijn de Vos, Victor Engmark'
__credits__ = ['Pepijn de Vos', 'Victor Engmark']
__maintainer__ = 'Victor Engmark'
__email__ = 'victor.engmark@gmail.com'
__license__ = 'GPL v3 or newer'
__url__ = 'https://github.com/l0b0/mian/wiki'
__version__ = '0.8.7'

from binascii import unhexlify
from getopt import getopt, GetoptError
from glob import glob
import matplotlib.pyplot as plt
from nbt.nbt import NBTFile
from operator import itemgetter
from os.path import join, split
from signal import signal, SIGPIPE, SIG_DFL
import sys
import warnings

from blocks import BLOCK_TYPES, UNUSED_NAME

HEX_DIGITS = '0123456789abcdef'

DEFAULT_BLOCK_TYPES = [
    'clay',
    'coal ore',
    'diamond ore',
    'gold ore',
    'iron ore',
    'obsidian',
    '49']

CHUNK_SIZE_Y = 128
CHUNK_SIZE_Z = 16
CHUNK_SIZE_X = CHUNK_SIZE_Y * CHUNK_SIZE_Z

LABEL_X = 'Layer'
LABEL_Y = 'Count'

signal(SIGPIPE, SIG_DFL)
"""Avoid 'Broken pipe' message when canceling piped command."""


def lookup_block_type(block_type):
    """
    Find block types based on input string.

    @param block_type: Name or hex ID of a block type.
    @return: Subset of BLOCK_TYPES.keys().
    """

    if block_type is None or len(block_type) == 0:
        warnings.warn('Empty block type')
        return []

    block_type = block_type.lower()

    if [char in HEX_DIGITS for char in block_type] == [True, True]:
        # 2 hex digits
        return [unhexlify(block_type)]

    # Name substring search, could have multiple results
    result = []
    for block_hex, block_names in BLOCK_TYPES.iteritems():  # Block
        for block_name in block_names:  # Synonyms
            if block_name.lower().find(block_type) != -1:
                result.append(block_hex)
    if result == []:
        warnings.warn('Unknown block type %s' % block_type)

    return result


def print_block_types():
    """Print the block block_names and hexadecimal IDs"""
    for block_hex, block_names in sorted(
        BLOCK_TYPES.iteritems(),
        key=itemgetter(0)):
        if block_names != [UNUSED_NAME]:
            sys.stdout.write(hex(ord(block_hex))[2:].upper().zfill(2) + ' ')
            sys.stdout.write(', '.join(block_names) + '\n')


def plot(counts, block_type_hexes, title):
    """
    Actual plotting of data.

    @param counts: Integer counts per layer.
    @param block_type_hexes: Subset of BLOCK_TYPES.keys().
    """
    fig = plt.figure()
    fig.canvas.set_window_title(title)

    for index, block_counts in enumerate(counts):
        plt.plot(
            block_counts,
            label=BLOCK_TYPES[block_type_hexes[index]][0],
            linewidth=1)

    plt.legend()
    plt.xlabel(LABEL_X)
    plt.ylabel(LABEL_Y)

    plt.show()


def mian(world_dir, block_type_hexes, nether):
    """
    Runs through the DAT files and gets the layer counts for the plot.

    @param world_dir: Path to existing Minecraft world directory.
    @param block_type_hexes: Subset of BLOCK_TYPES.keys().
    @param nether: Whether or not to graph The Nether.
    """

    title = split(world_dir)[1]

    # All world blocks are stored in DAT files
    if nether:
        paths = glob(join(world_dir, 'DIM-1/*/*/*.dat'))
        title += ' Nether'
    else:
        paths = glob(join(world_dir, '*/*/*.dat'))

    if paths == []:
        raise Usage('Invalid savegame path.')

    # Unpack block format
    # <http://www.minecraftwiki.net/wiki/Alpha_Level_Format#Block_Format>
    raw_blocks = ''
    for path in paths:
        nbtfile = NBTFile(path, 'rb')

        raw_blocks += nbtfile['Level']['Blocks'].value

        if 'close' in dir(nbtfile.file):
            nbtfile.file.close()

    layers = [raw_blocks[i::128] for i in xrange(127)]

    counts = [[] for i in xrange(len(block_type_hexes))]
    for bt_index in range(len(block_type_hexes)):
        bt_hex = block_type_hexes[bt_index]
        for layer in layers:
            counts[bt_index].append(layer.count(bt_hex))

    if counts == [[] for i in xrange(len(block_type_hexes))]:
        raise Usage('No blocks were recognized.')

    title += ' - mian ' + __version__

    plot(counts, block_type_hexes, title)


class Usage(Exception):
    """Command-line usage error"""
    def __init__(self, msg):
        super(Usage, self).__init__(msg)
        self.msg = msg + '\nSee --help for more information.'


def main(argv=None):
    """Argument handling."""

    if argv is None:
        argv = sys.argv

    # Defaults
    block_type_names = DEFAULT_BLOCK_TYPES
    nether = False

    try:
        try:
            opts, args = getopt(
                argv[1:],
                'b:lnh',
                ['blocks=', 'list', 'nether', 'help'])
        except GetoptError, err:
            raise Usage(str(err))

        for option, value in opts:
            if option in ('-b', '--blocks'):
                block_type_names = value.split(',')
            elif option in ('-n', '--nether'):
                nether = True
            elif option in ('-l', '--list'):
                print_block_types()
                return 0
            elif option in ('-h', '--help'):
                print __doc__
                return 0
            else:
                raise Usage('Unhandled option %s.' % option)

        if len(args) == 0:
            raise Usage('You need to specify a save directory.')

        if len(args) != 1:
            raise Usage('You need to specify exactly one save directory.')

        world_dir = args[0]

        # Look up block_types
        block_type_hexes = []
        for block_type_name in block_type_names:
            found_hexes = lookup_block_type(block_type_name)
            for found_hex in found_hexes:
                if found_hex not in block_type_hexes:  # Avoid duplicates
                    block_type_hexes.append(found_hex)

        mian(world_dir, block_type_hexes, nether)

    except Usage, err:
        sys.stderr.write(err.msg + '\n')
        return 2


if __name__ == '__main__':
    sys.exit(main())
