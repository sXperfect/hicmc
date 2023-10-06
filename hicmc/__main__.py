##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @copyright Institute fuer Informationsverarbeitung

import os
import logging as log
import argparse
import functools
import cooler
import fpzip
import numpy as np
import pandas as pd
from . import utils
from . import typing as t
from . import constants as consts
from . import statistics as stats
from . import domain
from .encode import encode_chromosome

parser = argparse.ArgumentParser(
    prog=consts.PROGRAM_NAME,
    description=consts.PROGRAM_DESC,
)
parser.add_argument('-l', '--log_level', help='log level', choices=consts.AVAIL_LOG_LEVELS.keys(), default='info')
parser.add_argument('--insulation_file', type=str)
parser.add_argument('--insulation_window', type=int)
parser.add_argument('--weights_precision', type=int, default=consts.WEIGHTS_PRECISION_DEFAULT)
parser.add_argument('--domain_mask_statistic', choices=stats.STATISTIC_FUNCS.keys(), default='deviation')
parser.add_argument('--domain_mask_threshold', type=float, default=1)
parser.add_argument('--domain_values_precision', type=int, default=consts.DOMAIN_VALUES_PRECISION_DEFAULT, help='Number of bits used for floating-point compression')
parser.add_argument('--distance_table_precision', type=int, default=consts.DISTANCE_TABLE_PRECISION_DEFAULT, help='Number of bits used for floating-point compression')
parser.add_argument('--balancing', type=str, default='KR')

parser.add_argument('input_file', type=str, help='input file path (.cool or .mcool)')
parser.add_argument('resolution', type=int)
parser.add_argument('output_directory', type=str)

def main(args):
    format_string = '[' + consts.PROGRAM_NAME + '] [%(asctime)s] [%(levelname)-8s] --- [%(processName)-11s] [%(filename)15s] [%(funcName)20s] %(message)s'
    log.basicConfig(format=format_string, level=log.INFO)

    utils.set_log_level(args.log_level)
    utils.print_banner()
    
    res = args.resolution
    input_file = args.input_file
    ins_win = args.insulation_window
    stat_name = args.domain_mask_statistic
    stat_f = stats.STATISTIC_FUNCS[stat_name]
    domain_mask_threshold, = args.domain_mask_threshold,
    weights_precision,  = args.weights_precision, 
    domain_values_precision,  = args.domain_values_precision, 
    distance_table_precision = args.distance_table_precision
    balancing_name = args.balancing

    #? Load cooler file
    store = cooler.Cooler(os.path.normpath(args.input_file) + f'::/resolutions/{args.resolution}')
    matrix_selector = store.matrix(balance=False)
    balancing_selector = store.bins()

    #? Setup output-directory
    output_directory_path = os.path.normpath(args.output_directory)
    if not os.path.exists(output_directory_path):
        os.makedirs(output_directory_path, exist_ok=True)

    #? Load insulation-table
    insulation_df = domain.load_insulation_table(args.insulation_file)
    if str(ins_win) not in insulation_df.columns:
        raise ValueError(
            f'Invalid insulation windows: {ins_win}. ' +  
            f'Available: {list(insulation_df.columns[3:])}'
        )
    insulation_rec = insulation_df.iloc[0]
    assert insulation_rec.end - insulation_rec.start == res, "Invalid insulation file for given resolution!"

    #? Iterate over all chromosomes, TODO: Add argument to select chromosome
    for chr_idx in range(len(store.chromnames)):
        chr_name = store.chromnames[chr_idx]

        log.info(
            f'Processing chromosome {chr_name} - {res}kb - {input_file}'
        )
        chr_dpath = os.path.join(output_directory_path, f'{chr_idx:02}-{chr_idx:02}')
        if not os.path.exists(chr_dpath):
            os.makedirs(chr_dpath)

        else:
            if len(os.listdir(chr_dpath)) == 8:
                log.info(f'Chromosome already processed!')
                continue

        #? Fetch contact-matrix from selector
        log.info(f'Fetching contact matrix...')
        contact_mat = matrix_selector.fetch(chr_name)
        contact_mat = contact_mat.astype(np.min_scalar_type(contact_mat.max()))
        stats.assert_square(contact_mat)

        #? Fetch balancing-weights from selector
        log.info(f'Fetching balancing weights...')
        balancing_weights = balancing_selector.fetch(chr_name)
        try:
            weights = balancing_weights[balancing_name]
        except:
            ValueError(f'Cannot found the balancing method: {balancing_name}')

        if consts.WEIGHTS_PRECISION_DEFAULT == 32:
            weights = weights.astype(np.float32)
        elif consts.WEIGHTS_PRECISION_DEFAULT == 64:
            weights = weights.astype(np.float64)
        else:
            raise ValueError(consts.WEIGHTS_PRECISION_DEFAULT)

        #? Load insulation boundaries for this chromosome
        log.info(f'Loading TAD boundaries...')
        boundary_mask = domain.select_boundaries(
            insulation_df,
            chr_name,
            args.insulation_window
        )

        log.info(f'Encoding contact matrix...')
        encode_chromosome(
            chr_dpath, 
            contact_mat, 
            weights, 
            boundary_mask,
            stat_f, 
            domain_mask_threshold,
            weights_precision, 
            domain_values_precision, 
            distance_table_precision
        )

if __name__ == '__main__':
    main(parser.parse_args())