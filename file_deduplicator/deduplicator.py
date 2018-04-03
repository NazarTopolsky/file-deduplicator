from typing import Iterable, Union
from .file_info import FileInfo
from .strategy import BaseStrategy

__all__ = ['Deduplicator']

DuplicateCollection = Iterable[Iterable[Union[FileInfo, str]]]


class Deduplicator(object):
    """
    Receives a duplicate collection, applies given Strategy to each
    duplicate list from collection.
    """

    def __init__(self, duplicates: DuplicateCollection,
                 strategy: BaseStrategy):
        self.duplicates = duplicates
        self.strategy = strategy

    def deduplicate(self):
        processed_list = []
        for duplicate_list in self.duplicates:
            processed_list.extend(self.strategy.process(duplicate_list))
        return processed_list
