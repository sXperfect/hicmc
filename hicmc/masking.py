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
    matrix:t.NDArray,
    axis: consts.Axis,
    mask: t.NDArray
) -> t.NDArray:

	nrows, ncols = matrix.shape
	if axis is consts.Axis.ROW:
		_out = np.zeros((len(mask), ncols), dtype=matrix.dtype)
		matrix_row = 0
		for index in range(len(mask)):
			if mask[index]:
				continue

			_out[index, :] = matrix[matrix_row, :]
			matrix_row += 1

		return _out

	if axis is t.Axis.Col:
		_out = np.zeros((nrows, len(mask)), dtype=matrix.dtype)
		matrix_col = 0
		for index in range(len(mask)):
			if mask[index]:
				continue

			_out[:, index] = matrix[:, matrix_col]
			matrix_col += 1

		return _out