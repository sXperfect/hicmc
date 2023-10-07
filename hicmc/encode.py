##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @file Description
# @copyright Institute fuer Informationsverarbeitung

import os
import json
import shutil
import logging as log
import numpy as np
import cooler
import fpzip
from . import typing as t
from . import constants as consts
from . import statistics as stats
from . import masking
from . import serializer
from . import transform
from . import domain
from .decode import decode_chromosome
from .wrapper import jbig, ppmd

def encode_chromosome(
    output_path: str,
    contact_mat:t.NDArray,
    weights:t.NDArray,
    boundary_mask:t.NDArray,
    stat_f:t.Statistic,
    domain_mask_threshold:float,
    weights_precision:int,
    domain_values_precision:int,
    distance_table_precision:int
):

    #? Generate distance-matrix
    n = contact_mat.shape[0]
    dist_mat = transform.gen_dist_mat(n)

    #? Apply row-masking
    contact_mat, mask = masking.mask_axis(contact_mat, consts.Axis.ROW)
    dist_mat = dist_mat[~mask, :]

    #? Apply col-masking
    contact_mat, mask = masking.mask_axis(contact_mat, consts.Axis.COL)
    dist_mat = dist_mat[:, ~mask]

    #? Save row-/col-mask (only save one for intra-chromosomal)    
    _payload = serializer.encode_binary_array(mask, True)
    with open(os.path.join(output_path, 'mask.bin'), 'wb') as file:
        file.write(_payload)

    weights = weights[~mask]
    weights = np.nan_to_num(weights, nan=1)

    #? Save balancing-weights
    _payload = fpzip.compress(weights, precision=weights_precision)
    with open(os.path.join(output_path, 'weights.fpzip'), 'wb') as file:
        file.write(_payload)

    #? Reload balancing-weights (because of lossy compression)
    weights = np.squeeze(fpzip.decompress(_payload))
    if weights.ndim == 0:
        weights = np.array([weights])

    balanced_contact_mat = transform.balance_matrix(contact_mat, weights)
    boundary_mask = boundary_mask[~mask]

    #? Save insulation-boundaries
    _payload = serializer.encode_binary_array(boundary_mask, True)
    with open(os.path.join(output_path, 'boundaries.bin'), 'wb') as file:
        file.write(_payload)

    # TODO: Add boundaries at mask-transition
    boundaries = np.argwhere(boundary_mask).reshape(-1)

    #? Generate domain-mask
    domain_mask = stats.map_domains(
        balanced_contact_mat, 
        boundaries, 
        stat_f
    ) > domain_mask_threshold

    #? Encode domain-mask using JBIG
    _temp = transform.transform_diagonal_mode0(domain_mask)
    _payload = jbig.encode_binary_matrix(_temp)
    with open(os.path.join(output_path, 'domain-mask.jbig'), 'wb') as file:
        file.write(_payload)

    #? Build domain-model
    domain_values, dist_table = domain.build_model(
        balanced_contact_mat, 
        dist_mat, 
        boundaries, 
        stats.STATISTIC_FUNCS['average'], 
        domain_mask
    )

    #? Save domain-values using fpZIP
    _payload = fpzip.compress(domain_values, precision=domain_values_precision)
    with open(os.path.join(output_path, 'domain-values.fpizp'), 'wb') as file:
        file.write(_payload)

    #? Reload domain-values (because of lossy compression)
    domain_values = np.reshape(fpzip.decompress(_payload), -1)

    #? Save distance-table
    _payload = fpzip.compress(dist_table, precision=distance_table_precision)
    with open(os.path.join(output_path, 'distance-table.fpizp'), 'wb') as file:
        file.write(_payload)

    #? Reload distance-table (because of lossy compression)
    dist_table = np.reshape(fpzip.decompress(_payload), -1)

    #? Reconstruct model
    model = domain.reconstruct_model(
        dist_mat, 
        boundaries, 
        domain_mask, 
        domain_values, 
        dist_table
    )
    model = transform.revert_balanced_matrix(model, weights)

    #? Transform original contact-matrix
    contact_mat = transform.transform_argsort(contact_mat, model)
    contact_mask, contact_data = transform.transform_split(contact_mat)

    #? Save contact-mask
    _payload = jbig.encode_binary_matrix(contact_mask)
    with open(os.path.join(output_path, 'contact-mask.jbig'), 'wb') as file:
        file.write(_payload)

    #? Save contact-data
    bytes_per_val = contact_data.dtype.itemsize
    _payload = ppmd.encode_bytes(contact_data.tobytes(), model_order=bytes_per_val*2)
    with open(os.path.join(output_path, 'contact-data.ppmd'), 'wb') as file:
        file.write(_payload)
        
def encode(args):    
    overwrite = args.overwrite
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
    
    log.info(f'Encoding {input_file}')

    #? Load cooler file
    store = cooler.Cooler(os.path.normpath(input_file) + f'::/resolutions/{res}')
    matrix_selector = store.matrix(balance=False)
    balancing_selector = store.bins()
    chr_names = store.chromnames

    #? Setup output-directory
    output_dpath = os.path.normpath(args.output_directory)
    if not os.path.exists(output_dpath):
        os.makedirs(output_dpath)
    else:
        if overwrite:
            shutil.rmtree(output_dpath)
            os.makedirs(output_dpath)
            
    meta_fpath = os.path.join(output_dpath, 'chr_names.json')
    meta_dict = {
        'res': res,
        'chr_names': chr_names
    }
    with open(meta_fpath, 'w') as f:
        json.dump(meta_dict, f, indent=4)

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
    for chr_idx in range(len(chr_names)):
        chr_name = chr_names[chr_idx]

        log.info(f'Processing chromosome {chr_name} at {res}kb')
        chr_dpath = os.path.join(output_dpath, f'{chr_idx:02}-{chr_idx:02}')
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
            ins_win
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
        
        if args.check_result:
            recon_contact_mat = decode_chromosome(
                chr_dpath
            )
            
            assert np.array_equal(contact_mat, recon_contact_mat), \
                "Decoded contact matrix differ from the original contact matrix"