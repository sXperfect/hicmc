import functools
import numpy as np
import pandas as pd
from . import typing as t
from . import constants as consts
from . import statistics as stats
from . import transform

def _insulation_remove_prefix(string: str, prefix: str) -> str:
    if string.startswith(prefix):
        return string[len(prefix):]

    return string

def _insulation_windows(table: pd.DataFrame) -> t.List[int]:
    _prefix = 'log2_insulation_score_'
    return [int(_insulation_remove_prefix(name, _prefix)) for name in filter(lambda string: string.startswith(_prefix), table.columns)] # type: ignore

def load_insulation_table(file_path: str):
    #? Load data-frame
    df = pd.read_csv(
        file_path,
        delimiter='\t',
        dtype=dict(chrom=str, region=str)
    )
    windows = _insulation_windows(df)

    #? Only load necessary columns
    _prefix = 'is_boundary_'
    cols = ['chrom', 'start', 'end'] + [_prefix + str(window) for window in windows]
    df = (
        df[cols]
        .rename(
            columns=functools.partial(
                _insulation_remove_prefix, 
                prefix=_prefix
            )
        )
    )
    return df

def select_boundaries(
    df:pd.DataFrame, 
    chr_name: str, 
    win_size: int
) -> t.NDArray[np.bool_]:
    
    df = (
        df[df.chrom == chr_name]
        .reset_index(drop=True)
    )
    return df[str(win_size)].to_numpy()

def _transform_domain_values(
    domain_values:t.NDArray, 
    domain_mask:t.NDArray
) -> t.NDArray:
    
    _domain_values = transform.transform_diagonal_mode0(domain_values)
    _domain_mask = transform.transform_diagonal_mode0(domain_mask)
    return _domain_values[~_domain_mask]


def _inverse_transform_domain_values(
    transformed:t.NDArray, 
    domain_mask: t.NDArray
) -> t.NDArray:
    
    _domain_mask = transform.transform_diagonal_mode0(domain_mask)
    _domain_values = np.zeros(_domain_mask.shape, transformed.dtype)
    _domain_values[~_domain_mask] = transformed

    return transform.inverse_tranform_diagonal_mode0(_domain_values)

def _transform_distance_table(
    dist_table:t.NDArray,
    dist_ids: t.NDArray
):
    
    max_dist = dist_table.shape[0]
    return np.concatenate([dist_table[dist, :dist_ids[dist]] for dist in range(max_dist)])

def _inverse_transfrom_distance_table(
    transformed: t.NDArray, 
    dist_ids: t.NDArray[np.integer]
) -> t.NDArray:
    
    trans_idx = 0
    _out = np.zeros((len(dist_ids), dist_ids.max()))
    for distance, entries in enumerate(dist_ids):
        _out[distance,:entries] = transformed[trans_idx:trans_idx+entries]
        trans_idx += entries

    return _out

def _recon_dist_ids(
    distances: t.NDArray[np.integer], 
    boundaries: t.NDArray, 
    domain_mask: t.NDArray[np.bool_]
) -> t.NDArray[np.integer]:
    
    #? Type-check input
    n = stats.assert_square(distances, return_n=True)

    #? Initialize distance-index
    domain_count = len(boundaries) + 1
    distance_index = np.zeros((distances.max() + 1), dtype=np.min_scalar_type(domain_count * 2))

    #? Iterate over all domain-indices in the upper-triangle (because contact-matrix is symmetric)
    for row_index, col_index in np.ndindex((domain_count, domain_count)):
        if col_index < row_index:
            continue

        #? Calculate row-/col-indices of domain-matrix
        row_start = boundaries[row_index - 1] if not row_index == 0 else 0
        row_end = boundaries[row_index] if not row_index == len(boundaries) else n
        col_start = boundaries[col_index - 1] if not col_index == 0 else 0
        col_end = boundaries[col_index] if not col_index == len(boundaries) else n

        #? The domain-mask indicates wheter simple or complex model is used
        if not domain_mask[row_index, col_index]:
            continue
        
        #? Increment distance-index
        distance_index[np.unique(distances[row_start:row_end, col_start:col_end])] += 1

    return distance_index

def build_model(
    balanced_contact_mat:t.NDArray,
    dist_mat:t.NDArray,
    boundaries:t.NDArray,
    stat_f:t.Statistic,
    domain_mask:t.NDArray
):

    #? Type-check input
    n = stats.assert_square(balanced_contact_mat, return_n=True)
    
    #? Calculate domain-values
    domain_values = stats.map_domains(balanced_contact_mat, boundaries, stat_f)
    if consts.DOMAIN_VALUES_PRECISION_DEFAULT == 32:
        domain_values = domain_values.astype(np.float32)

    elif consts.DOMAIN_VALUES_PRECISION_DEFAULT == 64:
        domain_values = domain_values.astype(np.float64)

    else:
        raise NotImplementedError(consts.DOMAIN_VALUES_PRECISION_DEFAULT)

    #? Initialize distance-table
    if consts.DISTANCE_TABLE_PRECISION_DEFAULT == 32:
        distance_table = np.zeros((dist_mat.max() + 1, np.sum(np.triu(domain_mask))), dtype=np.float32)

    elif consts.DISTANCE_TABLE_PRECISION_DEFAULT == 64:
        distance_table = np.zeros((dist_mat.max() + 1, np.sum(np.triu(domain_mask))), dtype=np.float64)

    else:
        raise NotImplementedError(consts.DISTANCE_TABLE_PRECISION_DEFAULT)

    #? Initialize distance-index
    ndomains = stats.assert_square(domain_mask, return_n=True)
    dist_indices = np.zeros((dist_mat.max() + 1), dtype=np.min_scalar_type(ndomains * 2))

    #? Iterate over all domain-indices in the upper-triangle (because contact-matrix is symmetric)
    for row_index, col_index in np.ndindex(domain_mask.shape):
        if col_index < row_index:
            continue
        
        #? Calculate row-/col-indices of domain-matrix
        row_start = boundaries[row_index - 1] if not row_index == 0 else 0
        row_end = boundaries[row_index] if not row_index == len(boundaries) else n
        col_start = boundaries[col_index - 1] if not col_index == 0 else 0
        col_end = boundaries[col_index] if not col_index == len(boundaries) else n

        #? The domain-mask indicates wheter simple or complex model is used
        if not domain_mask[row_index, col_index]:
            continue
        
        #? Generate intra-/inter-domain matrices
        domain_balanced_contact_mat = balanced_contact_mat[row_start:row_end, col_start:col_end]
        domain_dist_mat = dist_mat[row_start:row_end, col_start:col_end]

        #? Fill distance-table and increment distance-index
        for distance in np.unique(domain_dist_mat):
            distance_table[distance, dist_indices[distance]] = stat_f(
                domain_balanced_contact_mat[np.where(domain_dist_mat == distance)]
            )
            dist_indices[distance] += 1
    
    return (
        _transform_domain_values(domain_values, domain_mask), 
        _transform_distance_table(distance_table, dist_indices)
    )
    
def reconstruct_model(
    distances:t.NDArray[np.integer], 
    boundaries:t.NDArray, 
    domain_mask:t.NDArray[np.bool_], 
    domain_vals:t.NDArray, 
    dist_table:t.NDArray
):
    
    #? Type-check input
    n = stats.assert_square(distances, return_n=True)
    
    #? Reconstruct distance-index and distance-table
    distance_index = _recon_dist_ids(distances, boundaries, domain_mask)
    dist_table = _inverse_transfrom_distance_table(dist_table, distance_index)

    #? Initialize distance-index
    domain_count = len(boundaries) + 1
    distance_index = np.zeros((distances.max() + 1), dtype=np.min_scalar_type(domain_count * 2))

    #? Reconstruct domain-values
    domain_vals = _inverse_transform_domain_values(domain_vals, domain_mask)

    #? Initialize model-matrix
    if consts.MODEL_PRECISION == 32:
        model = np.zeros((n, n), dtype=np.float32)

    elif consts.MODEL_PRECISION == 64:
        model = np.zeros((n, n), dtype=np.float64)

    else:
        raise NotImplementedError(consts.MODEL_PRECISION)

    #? Iterate over all domain-indices in the upper-triangle (because contact-matrix is symmetric)
    for row_index, col_index in np.ndindex((domain_count, domain_count)):
        if col_index < row_index:
            continue
        
        #? Calculate row-/col-indices of domain-matrix
        row_start = boundaries[row_index - 1] if not row_index == 0 else 0
        row_end = boundaries[row_index] if not row_index == len(boundaries) else n
        col_start = boundaries[col_index - 1] if not col_index == 0 else 0
        col_end = boundaries[col_index] if not col_index == len(boundaries) else n

        #? The domain-mask indicates wheter simple or complex model is used
        if not domain_mask[row_index, col_index]:
            model[row_start : row_end, col_start : col_end] = domain_vals[row_index, col_index]
            continue

        #? Generate intra-/inter-domain matrices
        _distances = distances[row_start : row_end, col_start : col_end]
        _model = np.zeros(_distances.shape, dtype=model.dtype)

        #? Fill domain-model and increment distance-index
        for distance in np.unique(_distances):
            _model[np.where(_distances == distance)] = dist_table[distance, distance_index[distance]]
            distance_index[distance] += 1

        #? Copy domain-model
        model[row_start : row_end, col_start : col_end] = _model

    #? Copy upper-triangle to lower-triangle
    return transform.make_mat_symmetrical(model)