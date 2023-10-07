##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @file Description
# @copyright Institute fuer Informationsverarbeitung

import numpy as np
from . import typing as t
from . import constants as consts

def mask_axis(
    mat:t.NDArray,
    axis:consts.Axis
) -> t.Tuple[t.NDArray, t.NDArray[np.bool_]]:

	assert axis in [consts.Axis.ROW, consts.Axis.COL], "Invalid axis!"
	mask = ~np.any(mat, axis=axis.other.value)

	if axis is consts.Axis.ROW:
		mat = mat[~mask, :]
	elif axis is consts.Axis.COL:
		mat = mat[:, ~mask]
	else:
		raise RuntimeError("Invalid axis!")

	return mat, mask

def unmask_axis(
    mat:t.NDArray,
    axis: consts.Axis,
    mask: t.NDArray
) -> t.NDArray:

	nrows, ncols = mat.shape
	if axis is consts.Axis.ROW:
		out_mat = np.zeros((len(mask), ncols), dtype=mat.dtype)
		out_mat[~mask, :] = mat

	elif axis is consts.Axis.COL:
		out_mat = np.zeros((nrows, len(mask)), dtype=mat.dtype)
		out_mat[:, ~mask] = mat

	else:
		raise ValueError("Invalid axis:{axis}")

	return out_mat