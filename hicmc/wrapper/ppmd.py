import os
import subprocess
import tempfile
from enum import Enum

from .. import utils
from .. import constants as consts


MIN_MODEL_ORDER = 2
MAX_MODEL_ORDER = 16


_raw_file_name = 'raw.temp'
_out_file_name = 'out.temp'


_seven_zip_executable_path = os.path.join(consts.THIRD_PARTY_PATH, 'szip-x64', '7zz')
utils.check_executable(_seven_zip_executable_path)


class SevenZipCommand(Enum):
    Add = 'a'
    Benchmark = 'b'
    Delete = 'd'
    Extract = 'e'
    ListContent = 'l'


class SenvenZipMethod(Enum):
    PPMD = 'PPMd'


def encode_bytes(data: bytes, model_order: int = 8) -> bytes:
    if model_order < MIN_MODEL_ORDER:
        raise ValueError('Model-Order < 2 not valid!')

    if model_order > MAX_MODEL_ORDER:
        raise ValueError('Model-Order > 16 not valid!')

    with tempfile.TemporaryDirectory(prefix='7ZIP_') as directory_path:
        out_file_path = os.path.join(directory_path, _out_file_name)
        raw_file_path = os.path.join(directory_path, _raw_file_name)
        with open(raw_file_path, 'wb') as handle:
            handle.write(data)

        # Documentation: https://docs.python.org/3/library/subprocess.html#subprocess.run
        _command = SevenZipCommand.Add
        _method = SenvenZipMethod.PPMD
        process = subprocess.run([
            _seven_zip_executable_path,
            _command.value,
            f'-m0={_method.value}',
            f'-mo={model_order}',
            out_file_path,
            raw_file_path,
        ], stdout=subprocess.DEVNULL)

        if not process.returncode == 0:
            if process.stderr:
                raise RuntimeError(process.stderr.decode())

            if process.stdout:
                raise RuntimeError(process.stdout.decode())
            
            raise RuntimeError()
        
        if not os.path.exists(out_file_path):
            raise RuntimeError(f'Output-File does not exist, Path: {out_file_path}')

        with open(out_file_path, 'rb') as handle:
            return handle.read()
        

def decode_bytes(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix='7ZIP_') as directory_path:
        out_file_path = os.path.join(directory_path, _out_file_name)
        raw_file_path = os.path.join(directory_path, _raw_file_name)
        with open(raw_file_path, 'wb') as handle:
            handle.write(data)

        # Documentation: https://docs.python.org/3/library/subprocess.html#subprocess.run
        _command = SevenZipCommand.Extract
        _method = SenvenZipMethod.PPMD
        process = subprocess.run([
            _seven_zip_executable_path,
            _command.value,
            f'-m0={_method.value}',
            raw_file_path,
            f'-o{out_file_path}',
        ], stdout=subprocess.DEVNULL)

        if not process.returncode == 0:
            if process.stderr:
                raise RuntimeError(process.stderr.decode())

            if process.stdout:
                raise RuntimeError(process.stdout.decode())

            raise RuntimeError()
                
        if not os.path.exists(out_file_path):
            raise RuntimeError(f'Output-File does not exist, Path: {out_file_path}')

        with open(os.path.join(out_file_path, _raw_file_name), 'rb') as handle:
            return handle.read()