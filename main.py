import os.path
from profiler import Profiler
from file_deduplicator import Crawler, Deduplicator, get_strategy, dump_to_file, print_duplicates_size

BASE_PATH = 'D:\\folder'
DUPLICATES_DESTINATION = 'D:\\duplicates'
FOLDERS = [
    os.path.join(BASE_PATH, ''),
]


def deduplicate(duplicates):
    ordering = 'full_path_longest'
    strategy_type = 'move'
    strategy = get_strategy(
        strategy_type + ',' + ordering,
        out_base_path=DUPLICATES_DESTINATION,
        base_path=BASE_PATH,
    )
    d = Deduplicator(duplicates, strategy)
    d.deduplicate()


def main():
    crawler = Crawler(FOLDERS, allowed_extensions=[])
    crawler.crawl()
    dump_to_file(crawler)
    if not len(crawler.duplicates):
        print('No duplicates')
    else:
        print('Duplicate count: {}'.format(len(crawler.duplicates)))
        print_duplicates_size(crawler)
        deduplicate(crawler.duplicates)


if __name__ == '__main__':
    with Profiler():
        main()
