import os
import subprocess
import tempfile
from enum import IntFlag

import numpy
from PIL import Image

# from library import constants, utils
from .. import utils
from .. import constants as consts


Image.MAX_IMAGE_PIXELS = numpy.inf


_pbmtools_path = os.path.join(consts.THIRD_PARTY_PATH, 'jbigkit-2.1', 'pbmtools')


_pbmtojbg_path = os.path.join(_pbmtools_path, "pbmtojbg85")
utils.check_executable(_pbmtojbg_path)

_jbgtopbm_path = os.path.join(_pbmtools_path, "jbgtopbm85")
utils.check_executable(_jbgtopbm_path)


class JBIGOptions(IntFlag):
    DPON    =  4
    TPBON   =  8
    TPDON   = 16
    LRLTWO  = 64
    

PBM_TO_JBIG_DIRECTORY_PREFIX = 'PBM2JBIG_'
JBIG_TO_PBM_DIRECTORY_PREFIX = 'JBIG2PBM_'
PGM_TO_JBIG_DIRECTORY_PREFIX = 'PGM2JBIG_'


PIL_PBM_FORMAT = 'ppm'


def encode_binary_matrix(binary_matrix) -> bytes:
    with tempfile.TemporaryDirectory(prefix=PBM_TO_JBIG_DIRECTORY_PREFIX) as directory_path:
        pbm_file_path = os.path.join(directory_path, 'temp.pbm')
        jbg_file_path = os.path.join(directory_path, 'temp.jbg')

        # store matrix as PBM file using pillow library (https://pillow.readthedocs.io/en/stable/reference/Image.html)
        pbm_image = Image.fromarray(binary_matrix)
        pbm_image.save(pbm_file_path, format=PIL_PBM_FORMAT)
    
        # build arguments 
        options = JBIGOptions.TPBON | JBIGOptions.TPDON
        stripe_height = (1 << 32) - 1
        arguments = [
            "-s", str(stripe_height),
            "-p", str(options.value),
        ]

        process = subprocess.run([_pbmtojbg_path, *arguments, pbm_file_path, jbg_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            error_message = process.stderr.decode('utf-8')
            raise RuntimeError(error_message)

        with open(jbg_file_path, 'rb') as jbg_file_handle:
            payload_data = jbg_file_handle.read()

    return payload_data



def _get_shape(_payload):
    cols = _payload[4] << 24 | _payload[5] << 16 | _payload[ 6] << 8 | _payload[ 7]
    rows = _payload[8] << 24 | _payload[9] << 16 | _payload[10] << 8 | _payload[11]
    return rows, cols


def decode_binary_matrix(payload_data: bytes) -> numpy.ndarray:
    with tempfile.TemporaryDirectory(prefix=JBIG_TO_PBM_DIRECTORY_PREFIX) as directory_path:
        jbg_file_path = os.path.join(directory_path, 'temp.jbg')
        pbm_file_path = os.path.join(directory_path, 'temp.pbm')
        with open(jbg_file_path, 'wb') as jbg_file_handle:
            jbg_file_handle.write(payload_data)

        # build arguments
        rows, cols = _get_shape(payload_data)
        arguments = [
            "-x", str(cols),
            "-B", str(len(payload_data)),
        ]

        process = subprocess.run([_jbgtopbm_path, *arguments, jbg_file_path, pbm_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            error_message = process.stderr.decode('utf-8')
            raise RuntimeError(error_message)

        pbm_image = Image.open(pbm_file_path)

    matrix = numpy.asarray(pbm_image)
    return matrix
