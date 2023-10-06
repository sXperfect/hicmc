import os
import subprocess
import tempfile
from enum import Enum

from library import constants, utils


_raw_file_name = 'raw.temp'
_out_file_name = 'out.temp'


_bsc_executable_path = os.path.join(constants.third_party_directory_path, "bsc-3.2.4/build/bin/bsc")
utils.check_executable(_bsc_executable_path)


class BSCMode(Enum):
    Encode = 'e'
    Decode = 'd'


class BSCAlgorithm(Enum):
    Fast = 'e0'
    Static = 'e1'
    Adaptive = 'e2'


def encode_bytes(data: bytes, algorithm: BSCAlgorithm = BSCAlgorithm.Static) -> bytes:
    with tempfile.TemporaryDirectory(prefix='BSC_') as directory_path:
        out_file_path = os.path.join(directory_path, _out_file_name)
        raw_file_path = os.path.join(directory_path, _raw_file_name)
        with open(raw_file_path, 'wb') as handle:
            handle.write(data)

        mode = BSCMode.Encode
        process = subprocess.run([
            _bsc_executable_path,
            mode.value,
            raw_file_path,
            out_file_path,
            f'-{algorithm.value}', 
        ], stdout=subprocess.DEVNULL)

        if not process.returncode == 0:
            if process.stderr:
                raise RuntimeError(process.stderr.decode())

            raise RuntimeError()
                
        if not os.path.exists(out_file_path):
            raise RuntimeError(f'Output-File does not exist, Path: {out_file_path}')

        with open(out_file_path, 'rb') as handle:
            return handle.read()


def decode_bytes(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix='BSC_') as directory_path:
        out_file_path = os.path.join(directory_path, _out_file_name)
        raw_file_path = os.path.join(directory_path, _raw_file_name)
        with open(raw_file_path, 'wb') as handle:
            handle.write(data)

        mode = BSCMode.Decode
        process = subprocess.run([
            _bsc_executable_path,
            mode.value,
            raw_file_path,
            out_file_path,
        ], stdout=subprocess.DEVNULL)

        if not process.returncode == 0:
            if process.stderr:
                raise RuntimeError(process.stderr.decode())

            raise RuntimeError()
                
        if not os.path.exists(out_file_path):
            raise RuntimeError(f'Output-File does not exist, Path: {out_file_path}')

        with open(out_file_path, 'rb') as handle:
            return handle.read()