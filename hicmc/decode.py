##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @file Description
# @copyright Institute fuer Informationsverarbeitung

import os
import shutil
import json
import logging as log
import pandas as pd
import numpy as np
import fpzip
from . import typing as t
from . import constants as consts
from . import masking
from . import serializer
from . import transform
from . import domain
from .wrapper import jbig, ppmd

def decode_chromosome(
    input_path:str
) -> t.NDArray[np.integer]:
    
    #? Load row-/col-mask
    with open(os.path.join(input_path, 'mask.bin'), 'rb') as file:
        mask = serializer.decode_binary_array(file.read())
    
    #? Build distance-matrix
    dist_mat = transform.gen_dist_mat(len(mask))
    dist_mat = dist_mat[~mask, :]
    dist_mat = dist_mat[:, ~mask]

    #? Load balancing-weights
    with open(os.path.join(input_path, 'weights.fpzip'), 'rb') as file:
        weights = np.squeeze(fpzip.decompress(file.read()))

    #? Load insulation-boundaries
    with open(os.path.join(input_path, 'boundaries.bin'), 'rb') as file:
        boundaries = serializer.decode_binary_array(file.read())

    boundaries = np.where(boundaries)[0]

    #? Load domain-mask
    with open(os.path.join(input_path, 'domain-mask.jbig'), 'rb') as file:
        _temp = jbig.decode_binary_matrix(file.read())

    domain_mask = transform.inverse_tranform_diagonal_mode0(_temp)

    #? Load domain-values
    with open(os.path.join(input_path, 'domain-values.fpizp'), 'rb') as file:
        domain_values = np.reshape(fpzip.decompress(file.read()), -1)

    #? Load distance-table
    with open(os.path.join(input_path, 'distance-table.fpizp'), 'rb') as file:
        dist_table = np.reshape(fpzip.decompress(file.read()), -1) 

    #? Reconstruct model
    model = domain.reconstruct_model(
        dist_mat, 
        boundaries, 
        domain_mask, 
        domain_values, 
        dist_table
    )
    model = transform.revert_balanced_matrix(model, weights)

    #? Load contact-mask
    with open(os.path.join(input_path, 'contact-mask.jbig'), 'rb') as file:
        contact_mask = jbig.decode_binary_matrix(file.read())
    
    #? Load contact-data
    with open(os.path.join(input_path, 'contact-data.ppmd'), 'rb') as file:
        _buffer = ppmd.decode_bytes(file.read())
        _bytes = len(_buffer) // np.sum(contact_mask)
        if _bytes == 1:
            contact_data = np.frombuffer(_buffer, np.uint8)

        elif _bytes == 2:
            contact_data = np.frombuffer(_buffer, np.uint16)

        elif _bytes == 4:
            contact_data = np.frombuffer(_buffer, np.uint32)

        elif _bytes == 8:
            contact_data = np.frombuffer(_buffer, np.uint64)

        else: 
            raise NotImplementedError(_bytes)

    #? Reconstruct original contact-matrix
    contact_mat = transform.inverse_transform_split(contact_mask, contact_data)
    contact_mat = transform.inverse_transform_argsort(contact_mat, model)

    #? Remove row-/col-masking
    contact_mat = masking.unmask_axis(contact_mat, consts.Axis.ROW, mask) 
    contact_mat = masking.unmask_axis(contact_mat, consts.Axis.COL, mask) 

    return contact_mat

def decode(args):
    
    overwrite = args.overwrite
    dry_run = args.dry_run
    input_dpath = args.input
    output_dpath = args.output
    
    #? Setup output-directory
    output_dpath = os.path.normpath(output_dpath)
    if not dry_run:
        if not os.path.exists(output_dpath):
            os.makedirs(output_dpath)
        else:
            if overwrite:
                shutil.rmtree(output_dpath)
                os.makedirs(output_dpath)
    
    meta_fpath = os.path.join(input_dpath, 'chr_names.json')
    with open(meta_fpath, 'r') as f:
        meta_dict = json.load(f)
        
    chr_names = meta_dict['chr_names']
    res = meta_dict['res']
    
    for chr_idx, chr_name in enumerate(chr_names):

        log.info(f'Processing chromosome {chr_name} at {res}kb')
        chr_dpath = os.path.join(input_dpath, f'{chr_idx:02}-{chr_idx:02}')
        
        contact_mat = decode_chromosome(chr_dpath)
        
        if not dry_run:
            triu_contact_mat = np.triu(contact_mat)
            row_ids, col_ids = np.where(triu_contact_mat)
            
            df = pd.DataFrame(
                data={
                    'row_ids':row_ids, 
                    'col_ids':col_ids, 
                    'counts':triu_contact_mat[row_ids, col_ids]
                }
            )
            
            out_csv_fpath = os.path.join(output_dpath, f'{chr_idx:02}-{chr_idx:02}.csv')
            df.to_csv(
                out_csv_fpath,
                index=False
            )