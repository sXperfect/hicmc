import operator
import numpy as np
from . import typing as t

def encode_binary_run_length(arr):
    first_val = arr[0]
    rl_vect = np.where(np.diff(arr))[0] + 1
    rl_vect[1:] = np.diff(rl_vect)

    dtype = np.min_scalar_type(rl_vect.max())
    rl_vect = rl_vect.astype(dtype)
    
    rest = int(len(arr) - rl_vect.sum())
    if rest != 0:
        rl_vect = np.concatenate((rl_vect, [rest]))
        
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

    # TODO: matrix at this points is already symmetrical
    #? Check if matrix is symmetrical, otherwise enforce symmetry
    if not np.diag(balanced_mat, -1).any():
        balanced_mat = np.triu(balanced_mat) + np.triu(balanced_mat, 1).T
        
    return balanced_mat