##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @copyright Institute fuer Informationsverarbeitung

import os
import shutil
import logging as log
import argparse
import numpy as np
from . import utils
from . import typing as t
from . import constants as consts
from . import statistics as stats
from . import domain
from .encode import encode
from .decode import decode

parser = argparse.ArgumentParser(
    prog=consts.PROGRAM_NAME,
    description=consts.PROGRAM_DESC,
)
parser.add_argument('-l', '--log_level', help='log level', choices=consts.AVAIL_LOG_LEVELS.keys(), default='info')
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--overwrite', action='store_true')
subparsers = parser.add_subparsers(dest='mode', help='Mde, either ENCODE or DECODE')

encode_parser = subparsers.add_parser('ENCODE')
encode_parser.add_argument('--check-result', action='store_true', help="Check the decoded contact matrix equals the original matrix")
encode_parser.add_argument('--insulation-file', type=str)
encode_parser.add_argument('--insulation-window', type=int)
encode_parser.add_argument('--insulation-window-mult', type=int)
encode_parser.add_argument('--weights-precision', type=int, default=consts.WEIGHTS_PRECISION_DEFAULT)
encode_parser.add_argument('--domain-mask-statistic', choices=stats.STATISTIC_FUNCS.keys(), default='deviation')
encode_parser.add_argument('--domain-mask-threshold', type=float, default=1)
encode_parser.add_argument('--domain-values-precision', type=int, default=consts.DOMAIN_VALUES_PRECISION_DEFAULT, help='Number of bits used for floating-point compression')
encode_parser.add_argument('--distance-table-precision', type=int, default=consts.DISTANCE_TABLE_PRECISION_DEFAULT, help='Number of bits used for floating-point compression')
encode_parser.add_argument('--balancing', type=str, default='KR', help='Select a balancing method, default: KR')
encode_parser.add_argument('input_file', type=str, help='input file path (.cool or .mcool)')
encode_parser.add_argument('resolution', type=int)
encode_parser.add_argument('output_directory', type=str)

decode_parser = subparsers.add_parser('DECODE')
decode_parser.add_argument('input', type=str, help='Path to the HiCMC encoded payload')
decode_parser.add_argument('output', type=str, help='Output directory')

if __name__ == '__main__':
    args = parser.parse_args()
    
    format_string = '[' + consts.PROGRAM_NAME + '] [%(asctime)s] [%(levelname)-8s] --- [%(processName)-11s] [%(filename)15s] [%(funcName)20s] %(message)s'
    log.basicConfig(format=format_string, level=log.INFO)

    utils.set_log_level(args.log_level)
    utils.print_banner()
    
    if args.mode == 'ENCODE':
        encode(args)
    elif args.mode == 'DECODE':
        # raise NotImplementedError(f'Mode not yet implemented: {args.mode}')
        decode(args)
    else:
        raise ValueError(f'Invalid value for mode: {args.mode}')