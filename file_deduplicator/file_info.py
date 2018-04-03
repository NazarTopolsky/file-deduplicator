import os
import hashlib

__all__ = ['FileInfo']

_block_size = 65536


class FileInfo(object):
    def __init__(self, full_path):
        self.full_path = full_path
        self.size, self.modification_date = self._get_stats()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return 'FileInfo: {}'.format(self.full_path)

    def __eq__(self, other):
        if self.size != other.size:
            return False
        else:
            return self.hash == other.hash

    def __ne__(self, other):
        return not FileInfo.__eq__(self, other)

    @property
    def hash(self):
        """Lazy property to avoid calculating hash unless necessary"""
        try:
            return self.__hash_cache
        except AttributeError:
            self.__hash_cache = self._calculate_hash()
            return self.__hash_cache

    @property
    def dir_path(self):
        """Get directory"""
        head, tail = os.path.split(self.full_path)
        return head

    @property
    def filename(self):
        try:
            return self._filename
        except AttributeError:
            head, tail = os.path.split(self.full_path)
            self._filename = tail or os.path.split(head)[0]
            return self._filename

    def _get_filename(self):
        head, tail = os.path.split(self.full_path)
        return tail or os.path.split(head)[0]

    def _get_stats(self):
        stat = os.stat(self.full_path, follow_symlinks=False)
        return stat.st_size, stat.st_mtime

    def _calculate_hash(self):
        hasher = hashlib.sha256()
        with open(self.full_path, 'rb') as f:
            buf = f.read(_block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(_block_size)
            return hasher.digest()
