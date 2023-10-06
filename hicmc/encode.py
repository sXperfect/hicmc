import os
import numpy as np
import fpzip
# from scipy.spatial.distance import pdist, squareform
from . import typing as t
from . import constants as consts
from . import statistics as stats
from . import masking
from . import serializer
from . import transform
from .wrapper import jbig, ppmd

def _gen_dist_mat(
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

    # Generate distance-matrix
    n = contact_mat.shape[0]
    dist_mat = _gen_dist_mat(n)

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

    # Generate domain-mask
    domain_mask = stats.map_domains(
        balanced_contact_mat, 
        boundaries, 
        stat_f
    ) > domain_mask_threshold

    # Encode domain-mask using JBIG
    _temp = transform.transform_diagonal(domain_mask)
    _payload = jbig.encode_binary_matrix(_temp)
    with open(os.path.join(output_path, 'domain-mask.jbig'), 'wb') as file:
        file.write(_payload)

    # Build domain-model
    domain_values, distance_table = _build_model(balanced_contact_mat, dist_mat, boundaries, numpy.average, domain_mask)

    # Save domain-values using fpZIP
    _payload = fpzip.compress(domain_values, precision=domain_values_precision)
    with open(os.path.join(output_path, 'domain-values.fpizp'), 'wb') as file:
        file.write(_payload)

    # Reload domain-values (because of lossy compression)
    domain_values = numpy.reshape(fpzip.decompress(_payload), -1)

    # Save distance-table
    _payload = fpzip.compress(distance_table, precision=distance_table_precision)
    with open(os.path.join(output_path, 'distance-table.fpizp'), 'wb') as file:
        file.write(_payload)

    # Reload distance-table (because of lossy compression)
    distance_table = numpy.reshape(fpzip.decompress(_payload), -1)

    # Reconstruct model
    model = _reconstruct_model(dist_mat, boundaries, domain_mask, domain_values, distance_table)
    model = balance.deply(model, weights)

    # Transform original contact-matrix
    contact_mat = transform.transform_argsort(contact_mat, model)
    contact_mask, contact_data = transform.transform_split(contact_mat)

    # Save contact-mask
    _payload = jbig.encode_binary_matrix(contact_mask)
    with open(os.path.join(output_path, 'contact-mask.jbig'), 'wb') as file:
        file.write(_payload)

    # Save contact-data
    _payload = ppmd.encode_bytes(contact_data.tobytes(), model_order=contact_data.dtype.itemsize * 2)
    with open(os.path.join(output_path, 'contact-data.ppmd'), 'wb') as file:
        file.write(_payload)