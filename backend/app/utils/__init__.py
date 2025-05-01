from os import path as path_tool, PathLike

from .db_wrapper import AsyncDBWrapper, DBWrapper
from .lazy import lazy_bound_function, lazy_load_function
from .ranges import TimeRange, AnyTime
from .saver import save_analyzation_output, load_analyzation_output  # , load_heatmap, save_heatmap


def change_ext(path: PathLike, ext: str):
    return path_tool.splitext(path)[0] + ext