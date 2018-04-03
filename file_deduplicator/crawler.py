import os.path
from collections import defaultdict
from .file_info import FileInfo

__all__ = ['Crawler']


class BaseCrawler(object):
    def __init__(self, base_paths, allowed_extensions=None, recursive=True):
        self.base_paths = base_paths
        self.allowed_extensions = self._extensions(allowed_extensions)
        self.recursive = recursive

    def crawl(self):
        raise NotImplementedError

    @property
    def duplicates(self):
        try:
            return self._duplicate_cache
        except AttributeError:
            self._duplicate_cache = list(self.get_duplicate_groups())
            return self._duplicate_cache

    def get_duplicate_groups(self):
        raise NotImplementedError

    def write_to_stream(self, stream):
        for dup_list in self.duplicates:
            stream.write('#### ({} duplicates)\n'.format(len(dup_list)))
            stream.write('\n'.join(x.full_path for x in dup_list))
            stream.write('\n\n')

    @staticmethod
    def _extensions(extensions):
        if extensions is None:
            return []
        else:
            _extensions = []
            for extension in extensions:
                if not extension.startswith('.'):
                    extension = '.' + extension
                extensions.append(extension)
            return _extensions


class Crawler(BaseCrawler):
    def __init__(self, base_paths, allowed_extensions=None, recursive=True):
        super(Crawler, self).__init__(base_paths, allowed_extensions, recursive)
        self.storage = Storage()
        self.errors = []

    def crawl(self):
        if hasattr(self, '_duplicate_cache'):
            del self._duplicate_cache
        for directory, filename in self._get_files():
            self._process_file(directory, filename)

    def get_duplicate_groups(self):
        return self.storage.get_groups()

    def write_to_stream(self, stream):
        for dup_list in self.duplicates:
            stream.write('#### ({} duplicates)\n'.format(len(dup_list)))
            stream.write('\n'.join(x.full_path for x in dup_list))
            stream.write('\n\n')

    def _get_files(self):
        for base_path in self.base_paths:
            if self.recursive:
                for directory, subdirectories, files in os.walk(base_path):
                    for filename in files:
                        yield directory, filename
            else:
                for filename in os.listdir(base_path):
                    yield base_path, filename

    def _process_file(self, directory, filename):
        if self._file_allowed(filename):
            full_path = os.path.join(directory, filename)
            try:
                file_info = FileInfo(full_path)
                self.storage.add(file_info)
            except OSError:
                self.errors.append(full_path)

    def _file_allowed(self, filename):
        if self.allowed_extensions:
            return any(filename.endswith(x) for x in self.allowed_extensions)
        else:
            return True


class Storage(object):
    def __init__(self):
        self._storage = {}

    def add(self, file_info: FileInfo):
        try:
            self._storage[file_info.size].add(file_info)
        except KeyError:
            self._storage[file_info.size] = FileList(file_info.size)
            self._storage[file_info.size].add(file_info)

    def get_groups(self):
        for inline_list in self._storage.values():
            for group in inline_list.groups():
                if len(group) > 1:
                    yield group


class FileList(object):
    def __init__(self, file_size):
        self.file_size = file_size
        self.single_item = None
        self._is_single_file = True

    def __hash__(self):
        return self.file_size

    def add(self, file_info: FileInfo):
        if self.single_item is None:
            self.single_item = file_info
        else:
            if self._is_single_file:
                self._is_single_file = False
                self._items[self.single_item.hash].append(self.single_item)
            self._items[file_info.hash].append(file_info)

    def groups(self):
        if self._is_single_file:
            return [[self.single_item]]
        else:
            return list(self._items.values())

    @property
    def _items(self):
        try:
            return self._items_cache
        except AttributeError:
            self._items_cache = defaultdict(list)
            return self._items_cache
