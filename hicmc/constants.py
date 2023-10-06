##
# @author Yeremia G. Adhisantoso <adhisant@tnt.uni-hannover.de>
# @file Description
# @copyright Institute fuer Informationsverarbeitung

import os
import enum
import logging as log
from git.repo import Repo
from . import typing as t

PROGRAM_NAME = 'HiCMC'
PROGRAM_LONGNAME = 'High-Efficiency Contact Matrix Compressor'
PROGRAM_DESC = PROGRAM_LONGNAME

def get_root_path() -> str:
    #? Documentation: https://gitpython.readthedocs.io/en/stable/reference.html#module-git.repo.base
    repository = Repo('.', search_parent_directories=True)

    _out = repository.working_tree_dir
    if not isinstance(_out, str):
        raise RuntimeError(f'Output is not a string, Type: {type(_out)}')

    return _out

ROOT_PATH = get_root_path()
THIRD_PARTY_PATH = os.path.join(ROOT_PATH, 'third-party')

AVAIL_LOG_LEVELS = {
    'critical': log.CRITICAL,
    'error': log.ERROR,
    'warning': log.WARNING,
    'info': log.INFO,
    'debug': log.DEBUG,
}

WEIGHTS_PRECISION_DEFAULT: t.Union[t.Literal[32], t.Literal[64]] = 32
DOMAIN_VALUES_PRECISION_DEFAULT: t.Union[t.Literal[32], t.Literal[64]] = 32
DISTANCE_TABLE_PRECISION_DEFAULT: t.Union[t.Literal[32], t.Literal[64]] = 32
MODEL_PRECISION: t.Union[t.Literal[32], t.Literal[64]] = 32

class Axis(enum.IntEnum):
    ROW = 0
    COL = 1

    @property
    def other(self) -> 'Axis':
        if self is Axis.ROW:
            return Axis.COL

        if self is Axis.COL:
            return Axis.ROW

        raise RuntimeError()