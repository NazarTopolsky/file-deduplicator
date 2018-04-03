from .crawler import *
from .deduplicator import *
from .file_info import *
from .ordering import *
from .strategy import *

MEGABYTE = 1024 * 1024.


def print_duplicates_size(crawler):
    total = 0
    for dup_list in crawler.duplicates:
        total += sum(x.size for x in dup_list[1:]) / MEGABYTE
    print('Duplicates take up {:.3f} MB'.format(total))


def dump_to_file(crawler, filename='duplicates'):
    with open(filename, 'w+', encoding='utf-8') as duplicates_file:
        crawler.write_to_stream(duplicates_file)
