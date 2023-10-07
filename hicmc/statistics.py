##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @file Description
# @copyright Institute fuer Informationsverarbeitung

import math
import numpy as np
from . import typing as t

def sparsity(array: t.NDArray) -> float:
    density = np.count_nonzero(array) / math.prod(array.shape)
    return 1 - density(array)

STATISTIC_FUNCS = {
    'average': np.average,
    'sparsity': sparsity,
    'deviation': np.std,
}

def assert_square(matrix: t.NDArray, return_n=False) -> int:
    nrows, ncols = matrix.shape
    if not nrows == ncols:
        raise RuntimeError(f'Matrix is not square, Shape: {matrix.shape}')

    if return_n:
        return nrows
    
def cumshift_cols(mat: t.NDArray, k: int) -> t.NDArray:
    n = assert_square(mat, return_n=True)

    #? Compute output-matrix
    out_mat = np.empty_like(mat)
    for index in range(n):
        out_mat[:, index] = np.roll(mat[:, index], k * index)

    return out_mat

def map_domains(
    contact_mat:t.NDArray[np.integer],
    boundaries:t.NDArray,
    stat_f:t.Statistic
) -> t.NDArray:

    #? Check input-type
    n = assert_square(contact_mat, return_n=True)

    ndomains = len(boundaries) + 1
    domain_mat_shape = (ndomains, ndomains)
    domain_mat = np.zeros(domain_mat_shape, dtype=np.floating)

    #? Iterate over all domain-indices in the upper-triangle (because contact-matrix is symmetric)
    for row_index, col_index in np.ndindex(domain_mat_shape):
        if col_index < row_index:
            continue
        
        #? Calculate row-/col-indices of domain-matrix
        row_start = boundaries[row_index - 1] if not row_index == 0 else 0
        row_end = boundaries[row_index] if not row_index == len(boundaries) else n
        col_start = boundaries[col_index - 1] if not col_index == 0 else 0
        col_end = boundaries[col_index] if not col_index == len(boundaries) else n

        #? Calculate statistic and write 
        domain_mat[row_index, col_index] = stat_f(contact_mat[row_start:row_end, col_start:col_end])

    #? Enforce symmetrical property
    if not np.diag(domain_mat, -1).any():
        domain_mat = np.triu(domain_mat) + np.triu(domain_mat, 1).T
        
    return domain_mat