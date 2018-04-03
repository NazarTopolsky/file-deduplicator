from functools import partial
from operator import attrgetter
import os.path
from typing import Iterable

__all__ = ['Ordering']


class Ordering(object):
    SIZE_ASCENDING = 'size_ascending'
    SIZE_DESCENDING = 'size_descending'
    NAME_ASCENDING = 'name_ascending'
    NAME_DESCENDING = 'name_descending'
    NAME_LONGEST = 'name_longest'
    NAME_SHORTEST = 'name_shortest'
    DATE_OLDEST = 'date_oldest'
    DATE_NEWEST = 'date_newest'
    FULL_PATH_LONGEST = 'full_path_longest'
    FULL_PATH_SHORTEST = 'full_path_shortest'

    @classmethod
    def get_orderings(cls):
        return {
            cls.SIZE_ASCENDING: _size_ordering,
            cls.SIZE_DESCENDING: partial(_size_ordering, reverse=True),
            cls.NAME_ASCENDING: _name_ordering,
            cls.NAME_DESCENDING: partial(_name_ordering, reverse=True),
            cls.NAME_LONGEST: partial(_name_length_ordering, reverse=True),
            cls.NAME_SHORTEST: partial(_name_length_ordering, reverse=False),
            cls.DATE_OLDEST: _date_ordering,
            cls.DATE_NEWEST: partial(_date_ordering, reverse=True),
            cls.FULL_PATH_SHORTEST: _path_length,
            cls.FULL_PATH_LONGEST: partial(_path_length, reverse=True),
        }

    @classmethod
    def get_ordering(cls, ordering_name: str, priority_paths: Iterable = None):
        ordering = cls.get_orderings()[ordering_name]
        if priority_paths:
            ordering = cls.get_priority_sorting(priority_paths, ordering)
        return ordering

    @staticmethod
    def get_priority_sorting(priority_paths, base_sorter):
        priority_paths = list(priority_paths)

        def check(item):
            a_file = os.path.abspath(item.full_path)
            for path in priority_paths:
                parent = os.path.abspath(path)
                if os.path.commonprefix([a_file, parent]) == os.path.commonpath([parent]):
                    return True
            return False

        def inner(duplicate_seq, _reverse):
            prioritised = []
            other = []
            for item in duplicate_seq:
                if check(item):
                    prioritised.append(item)
                else:
                    other.append(item)
            return (
                base_sorter(prioritised, _reverse) +
                base_sorter(other, _reverse)
            )
        return inner


def _size_ordering(duplicate_seq, reverse=False):
    return sorted(duplicate_seq, key=attrgetter('size'), reverse=reverse)


def _name_ordering(duplicate_seq, reverse=False):
    return sorted(duplicate_seq, key=attrgetter('filename'), reverse=reverse)


def _name_length_ordering(duplicate_seq, reverse=False):
    return sorted(duplicate_seq, key=lambda x: len(x.filename), reverse=reverse)


def _date_ordering(duplicate_seq, reverse=False):
    return sorted(duplicate_seq, key=attrgetter('modification_date'),
                  reverse=reverse)


def _path_length(duplicate_seq, reverse=False):
    return sorted(duplicate_seq, key=lambda x: len(x.full_path), reverse=reverse)
