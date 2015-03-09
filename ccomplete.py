from CComplete.tokenizer import Tokenizer
from CComplete.includescanner import IncludeScanner
import re, bisect

class CComplete:
    def __init__(self, cachesize = 500, cachepath = "/tmp"):
        self.cachesize = cachesize
        self.T = Tokenizer(cachepath, cachesize)
        self.I = IncludeScanner()
        self.tokens = {}
        self.functiontokens = {}

    def add_tokens(self, tokens):
        for tokenname in tokens:
            token=tokens[tokenname]
            lname = tokenname.lower()
            if lname in self.tokens:
                self.tokens[lname] = Tokenizer.best_match([self.tokens[lname], token])
            else:
                self.tokens[lname] = token

    def is_valid(self, filename, basepaths = [], syspaths = [], extra_files=[]):
        files = self.I.scan_recursive(filename, basepaths, syspaths)
        for file in extra_files:
            if file not in files:
                files.append(file)
        return self.T.files_valid(files)

    def load_file(self, filename, basepaths = [], syspaths = [], extra_files=[]):
        self.files = self.I.scan_recursive(filename, basepaths, syspaths)
        for file in extra_files:
            if file not in self.files:
                self.files.append(file)
        self.T.set_cache_size(max(self.cachesize, len(self.files)))
        self.tokens = {}
        self.functiontokens = {}
        self.sortedtokens = []
        for file in self.files:
            tokens, functokens = self.T.scan_file(file)
            self.add_tokens(tokens)
            self.functiontokens[file] = functokens
        self.sortedtokens = [x.lower() for x in self.tokens.keys()]
        self.sortedtokens.sort()
        rem = self.T.clean_cache(set(self.files))
        print("Removed %d entries" % rem)
        print("Done loading, %d files" % len(self.files))

    def search_tokens(self, prefix):
        prefix = prefix.lower()
        pos=bisect.bisect_left(self.sortedtokens, prefix)
        results=[]
        while pos < len(self.sortedtokens):
            if self.sortedtokens[pos].startswith(prefix):
                results.append(self.tokens[self.sortedtokens[pos]])
            else:
                break
            pos+=1
        return results
