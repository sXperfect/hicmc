import functools
import numpy as np
import pandas as pd
from . import typing as t

def _insulation_remove_prefix(string: str, prefix: str) -> str:
    if string.startswith(prefix):
        return string[len(prefix):]

    return string

def _insulation_windows(table: pd.DataFrame) -> t.List[int]:
    _prefix = 'log2_insulation_score_'
    return [int(_insulation_remove_prefix(name, _prefix)) for name in filter(lambda string: string.startswith(_prefix), table.columns)] # type: ignore

def load_insulation_table(file_path: str):
    #? Load data-frame
    df = pd.read_csv(
        file_path,
        delimiter='\t',
        dtype=dict(chrom=str, region=str)
    )
    windows = _insulation_windows(df)

    #? Only load necessary columns
    _prefix = 'is_boundary_'
    cols = ['chrom', 'start', 'end'] + [_prefix + str(window) for window in windows]
    df = (
        df[cols]
        .rename(
            columns=functools.partial(
                _insulation_remove_prefix, 
                prefix=_prefix
            )
        )
    )
    return df

def select_boundaries(
    df:pd.DataFrame, 
    chr_name: str, 
    win_size: int
) -> t.NDArray[np.bool_]:
    
    df = (
        df[df.chrom == chr_name]
        .reset_index(drop=True)
    )
    return df[str(win_size)].to_numpy()