import cProfile
import pstats
import io


class Profiler(object):
    def __init__(self, filename='profile.txt'):
        self.filename = filename

    def __enter__(self):
        self.pr = cProfile.Profile()
        self.pr.enable()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(self.pr, stream=s).sort_stats('tottime')
        ps.print_stats()
        with open(self.filename, encoding='utf-8', mode='w') as f:
            f.write(s.getvalue())
