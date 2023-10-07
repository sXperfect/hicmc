##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @file Description
# @copyright Institute fuer Informationsverarbeitung

import numpy as np
from . import typing as t
from . import statistics as stats

def gen_dist_mat(
    n:int
) -> t.NDArray[np.integer]:

    dist_mat_shape = (n, n)
    dist_mat_dtype = np.min_scalar_type(n - 1)
    dist_mat:t.NDArray[np.integer] = np.zeros(
        dist_mat_shape,
        dtype=dist_mat_dtype
    )

    for index in range(n):
        dist_mat[index, :] = index

    dist_mat = stats.cumshift_cols(dist_mat, 1)
    dist_mat = np.tril(dist_mat) + np.transpose(np.tril(dist_mat, -1))

    return dist_mat

def make_mat_symmetrical(mat, check=False):
    if not check or not np.diag(mat, -1).any():
        mat = np.triu(mat) + np.triu(mat, 1).T
        
    return mat
    

def encode_binary_run_length(arr):
    first_val = arr[0]
    rl_vect = np.where(np.diff(arr))[0] + 1
    rl_vect[1:] = np.diff(rl_vect)
    
    rest = int(len(arr) - rl_vect.sum())
    if rest != 0:
        rl_vect = np.concatenate((rl_vect, [rest]))
        
    dtype = np.min_scalar_type(rl_vect.max())
    rl_vect = rl_vect.astype(dtype)
        
    return first_val, rl_vect

def decode_binary_run_length(
    first_val: bool, 
    rl_vect:t.NDArray[np.integer]
) -> t.NDArray[np.bool_]:
    
    nentries = rl_vect.sum()
    mask = np.empty(nentries, dtype=np.bool_)

    start_idx = 0
    curr_val = first_val
    for rl in rl_vect:
        end_idx = start_idx+rl
        mask[start_idx:end_idx] = curr_val
        start_idx += rl
        curr_val = not curr_val

    mask[start_idx:] = curr_val
    return mask

def balance_matrix(
    mat:t.NDArray, 
    weights:t.NDArray, 
    mult_op:bool=False
) -> t.NDArray:
    
    balanced_mat = mat.astype(weights.dtype)
    weights = weights.reshape(-1, 1)
    
    if mult_op:
        balanced_mat *= weights
        balanced_mat *= weights.T

    else:
        balanced_mat /= weights
        balanced_mat /= weights.T

    return make_mat_symmetrical(balanced_mat, check=True)

def revert_balanced_matrix(
    matrix:t.NDArray,
    weights:t.NDArray,
    mult_op:bool = False
) -> t.NDArray:
    
    return balance_matrix(matrix, weights, not mult_op)

def transform_diagonal_mode0(
    mat:t.NDArray
):
    n = stats.assert_square(mat, return_n=True)
    offsets = np.concatenate([np.arange(n), -np.arange(1, n)])
    
    concatenated = np.concatenate([np.diagonal(mat, offset) for offset in offsets])
    transformed_mat = concatenated.reshape(mat.shape)
    
    target_nrows = n//2 + 1
    return transformed_mat[: target_nrows]

def inverse_tranform_diagonal_mode0(
    mat:t.NDArray
) -> t.NDArray:
    
    ncols = mat.shape[1]
    mat = mat.flatten()
    
    trans_idx = 0
    out_mat = np.zeros((ncols, ncols), dtype=mat.dtype)
    for idx in range(ncols):
        _entries = ncols - idx
        out_mat[ncols-idx-1,idx:] = mat[trans_idx:trans_idx+_entries]
        trans_idx += _entries

    out_mat = stats.cumshift_cols(out_mat, 1)
    out_mat = np.roll(out_mat, 1, axis=0)

    return make_mat_symmetrical(out_mat, check=True)

def transform_argsort(
    mat: t.NDArray, 
    model: t.NDArray
) -> t.NDArray:    

    #? Type-check input
    n = stats.assert_square(mat, return_n=True)

    transformed_rows = int(np.ceil((n + 1) / 2))

    #? Transform matrix
    mat = stats.cumshift_cols(mat, -1)
    mat = mat[: transformed_rows, :].copy()
    mat = mat.flatten()

    #? Transform model
    model = stats.cumshift_cols(model, -1)
    model = model[: transformed_rows, :].copy()
    model = model.flatten()

    #? Sort matrix using model
    assert len(mat) == len(model)
    mat = mat[np.argsort(model)]
    return mat.reshape((transformed_rows, n))


def inverse_transform_argsort(
    transformed: t.NDArray, 
    model: t.NDArray
):

    nrows, ncols = transformed.shape
    matrix_rows = ncols
    matrix_cols = ncols

    #? Transform model
    model = stats.cumshift_cols(model, -1)
    model = model[:nrows, :]
    
    transformed = transformed.flatten()
    transformed = transformed[np.argsort(np.argsort(model.flatten()))]
    transformed = transformed.reshape((nrows, ncols))

    out_mat = np.zeros((matrix_rows, matrix_cols), dtype=transformed.dtype)
    out_mat[:nrows, :] = transformed
    out_mat = stats.cumshift_cols(out_mat, 1)
    out_mat = np.tril(out_mat) + np.transpose(np.triu(out_mat, nrows))
    out_mat += np.triu(np.transpose(out_mat), 1)
    return out_mat


def transform_split(
    mat:t.NDArray
):
    return mat.astype(bool), mat[np.nonzero(mat)]

def inverse_transform_split(
    mask: t.NDArray[np.bool_], 
    data: t.NDArray[np.integer]
) -> t.NDArray[np.integer]:
    
    mat = np.zeros(mask.shape, data.dtype)
    mat[mask] = data
    return mat