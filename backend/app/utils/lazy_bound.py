import functools, importlib
from typing import Callable


def get_lazy_item(module_path: str, name: str):
    """
    Lazily loads an item from a module.
    """
    return getattr(importlib.import_module(module_path), name)


def lazy_bound_function(module_function_path: str):
    """
    Decorator to lazily bind a function from a module and pass it as `lazy_function` parameter.
    """
    
    def deco(function: Callable):
        module_function = None

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            nonlocal module_function

            if module_function is None:
                module_function = get_lazy_item(*module_function_path.rsplit('.', 1))

            return function(*args, lazy_function=module_function, **kwargs)
        
        return wrapper
    
    return deco


def lazy_load_function(module_function_path: str):
    """
    Utility to lazily bind a function from a module.
    """
    
    module_function = None

    def wrapper(*args, **kwargs):
        nonlocal module_function

        if module_function is None:
            module_function = get_lazy_item(*module_function_path.rsplit('.', 1))

        return module_function(*args, **kwargs)
    
    return wrapper