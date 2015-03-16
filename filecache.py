import os.path
import marshal

class FileCache:
    def __init__(self, filecache = False, cachepath = "/tmp", filesuffix = ""):
        self.cache = {}
        self.cachepath = cachepath
        self.filesuffix = filesuffix
        self.used = []
        self.filecache = filecache

    def clear_cache(self):
        self.cache = {}

    def get(self, filename):
        latest = os.path.getmtime(filename)
        if filename in self.cache:
            time, values = self.cache[filename]
            if time >= latest:
                self.used.remove(filename)
                self.used.insert(0, filename)
                return values
        if self.filecache:
            hashfn = os.path.join(self.cachepath, str(hash(filename))+self.filesuffix)
            if os.path.isfile(hashfn) and os.path.getmtime(hashfn) >= latest:
                with open(hashfn, 'rb') as f:
                    values = marshal.load(f)
                self.cache[filename] = (latest, values)
                return values
        return None

    def set(self, filename, values):
        latest = os.path.getmtime(filename)
        if filename in self.cache:
            self.used.remove(filename)
        self.used.insert(0, filename)
        self.cache[filename] = (latest, values)
        if self.filecache:
            hashfn = os.path.join(self.cachepath, str(hash(filename))+self.filesuffix)
            with open(hashfn, 'wb') as f:
                marshal.dump(values, f)

    def clean_cache(self):
        entries = list(self.cache.keys())
        for filename in entries:
            if not os.path.isfile(filename):
                del self.cache[filename]
                continue
            time, _ = self.cache[filename]
            if os.path.getmtime(filename) > time:
                del self.cache[filename]

    def clear_cache(self, limit):
        removes = self.used[limit:]
        self.used=self.used[:limit]
        for i in removes:
            del self.cache[i]