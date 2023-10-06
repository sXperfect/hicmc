import os
import logging as log
from . import constants as consts

def check_executable(file_path: str):
    if not os.path.isfile(file_path):
        raise RuntimeError(f'File does not exist: {file_path}')

    if not os.access(file_path, os.X_OK):
        raise RuntimeError(f'File is not executable: {file_path}')

def set_log_level(log_level):
    #? Log level
    try:
        log_level = consts.AVAIL_LOG_LEVELS[log_level]
    except KeyError:
        log.warning("invalid log level '%s' (using fall-back log level 'info')", log_level)
        log_level = log.INFO
    logger = log.getLogger()
    logger.setLevel(log_level)

def print_banner():
    #? Print banner
    log.info(f"********************************************************************************")
    log.info(f"    {consts.PROGRAM_LONGNAME} ({consts.PROGRAM_NAME})")
    log.info(f"********************************************************************************")