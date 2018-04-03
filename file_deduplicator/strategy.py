import errno

import os
import shutil
from typing import Callable, Iterable, Sized
from .file_info import FileInfo
from .ordering import Ordering

__all__ = ['get_strategy', 'CopyStrategy', 'MoveStrategy',
           'MoveAndRenameStrategy', 'BaseStrategy']


class BaseStrategy(object):
    @staticmethod
    def _enforce_file_info(duplicates):
        for item in duplicates:
            if isinstance(item, FileInfo):
                yield item
            else:
                yield FileInfo(item)

    def apply(self, item: FileInfo):
        raise NotImplementedError

    def process(self, duplicate_list):
        raise NotImplementedError


class MockStrategy(BaseStrategy):
    """Just print affected paths"""

    def __init__(self, ordering):
        self.ordering = ordering

    def apply(self, item: FileInfo):
        print(item.full_path)

    def process(self, duplicate_list):
        duplicates = self.ordering(duplicate_list)[1:]
        removed = []
        for item in self._enforce_file_info(duplicates):
            self.apply(item)
            removed.append(item.full_path)
        return removed


class DeleteStrategy(BaseStrategy):
    """Orders duplicates using given ordering, deletes all but first"""

    def __init__(self, ordering):
        self.ordering = ordering

    def apply(self, item):
        os.remove(item.full_path)

    def process(self, duplicate_list):
        duplicates = self.ordering(duplicate_list)[1:]
        removed = []
        for item in self._enforce_file_info(duplicates):
            self.apply(item)
            removed.append(item.full_path)
        return removed


class BaseMoveStrategy(BaseStrategy):
    """
    Base class for strategies that move/copy duplicates
    Recreates immediate directories in process
    """

    def __init__(self, ordering, out_base_path: str, base_path: str,
                 error_handler: Callable[[FileInfo], str]=None):
        """
        When moving file to out_out_base_path, will attempt to recreate
        intermediate directories.
        New path is calculated by concatenating the file path relative
        to base_path to out_base_path
        """
        self.ordering = ordering
        self.out_path = out_base_path
        self.base_path = base_path
        self.error_handler = error_handler

    @staticmethod
    def _apply_to_file(path_from, path_to):
        os.rename(path_from, path_to)

    def _get_relative_path(self, full_path):
        relative = os.path.relpath(full_path, self.base_path)
        if relative.startswith(os.pardir):
            raise ValueError('File {} is not in a subfolder of {}'.format(full_path, self.base_path))
        return os.path.join(self.out_path, relative)

    @staticmethod
    def _make_intermediate_directories(path):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:  # Guard against race conditions
            if exc.errno != errno.EEXIST:
                raise

    def apply(self, item):
        path = self._get_relative_path(item.full_path)
        self._make_intermediate_directories(path)
        # move the file
        try:
            self._apply_to_file(item.full_path, path)
            return path
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            elif self.error_handler is not None:
                return self.error_handler(item, path)

    def process(self, duplicate_list):
        duplicates = self.ordering(duplicate_list)[1:]
        moved = []
        for item in self._enforce_file_info(duplicates):
            moved.append(self.apply(item))
        return moved


class MoveStrategy(BaseMoveStrategy):
    """
    Move duplicates to specified out_base_path recreating intermediate
    directories
    """


class CopyStrategy(BaseMoveStrategy):
    """
    Copy duplicates to specified out_base_path recreating intermediate
    directories
    """

    @staticmethod
    def _apply_to_file(path_from, path_to):
        shutil.copyfile(path_from, path_to)


class MoveAndRenameStrategy(BaseMoveStrategy):
    """
    Move duplicates to specified out_base_path recreating intermediate
    directories.
    Unlike MoveStrategy, also renames original file (one not counted as
    a duplicate), using name_picker callable that accepts iterable of
    strings (default: MoveAndRenameStrategy.longest_name)
    """

    @staticmethod
    def longest_name(name_list: Iterable[Sized]):
        return sorted(name_list, key=len)[0]

    @staticmethod
    def shortest_name(name_list: Iterable[Sized]):
        return sorted(name_list, key=len, reverse=True)

    def __init__(self, ordering, out_base_path: str, base_path: str,
                 error_handler: Callable[[FileInfo], str]=None,
                 name_picker: Callable[[Iterable[str]], str]=longest_name):
        super().__init__(ordering, out_base_path, base_path, error_handler)
        if not callable(name_picker):
            raise TypeError('`name_picker` object must be callable')
        self.name_picker = name_picker

    @staticmethod
    def _rename_last_file(file_info: FileInfo, new_name: str):
        path = file_info.dir_path
        new_path = os.path.join(path, new_name)
        os.rename(file_info.full_path, new_path)

    def process(self, duplicate_list):
        file_list = self.ordering(duplicate_list)
        file_to_rename, duplicates = file_list[0], file_list[:1]
        moved = []
        name_list = []
        for item in self._enforce_file_info(duplicates):
            name_list.append(item.filename)
            moved.append(self.apply(item))
        new_name = self.name_picker(name_list)
        self._rename_last_file(file_to_rename, new_name)
        return moved


def get_strategy(strategy_str: str, priority_paths: Iterable = None, **kwargs):
    try:
        strategy, ordering = tuple(strategy_str.split(','))
    except ValueError:
        raise ValueError('strategy_str has incorrect format')
    strategy_cls = _get_strategy(strategy)
    order = Ordering.get_ordering(ordering, priority_paths)
    return strategy_cls(order, **kwargs)


def _get_strategy(strategy):
    strategies = {'remove': DeleteStrategy,
                  'delete': DeleteStrategy,
                  'move': MoveStrategy,
                  'copy': CopyStrategy,
                  'mock': MockStrategy,
                  'move_and_rename': MoveAndRenameStrategy}
    try:
        strategy_cls = strategies[strategy]
    except KeyError:
        raise ValueError('Unknown strategy: {}'.format(strategy))
    return strategy_cls
