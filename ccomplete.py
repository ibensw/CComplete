from CComplete.tokenizer import Tokenizer
from CComplete.includescanner import IncludeScanner
import re, bisect

class CComplete:
    def __init__(self, cachesize = 500):
        self.cachesize = cachesize
        self.T = Tokenizer(cachesize)
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

    @staticmethod
    def pretty_type(line):
        if line[0:2] == "/^" and line[-2:] == "$/":
            line = line[2:-2]
        type = Tokenizer.parsevariable(line)
        if not type:
            return ""
            # return line.lstrip().split()[0]
        ret=type[1]
        if type[2]:
            ret="*"+ret
        if type[3]:
            ret=ret+type[3]
        return ret

    def prettify(self, tokens):
        for tokenname in tokens:
            token = tokens[tokenname]
            if "status" in token[Tokenizer.T_EXTRA]:
                return

            if token[Tokenizer.T_KIND] == "f":
                token[Tokenizer.T_EXTRA]["status"]="Func: $#" + token[Tokenizer.T_EXTRA]["signature"]
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t()", token[Tokenizer.T_NAME]+token[Tokenizer.T_EXTRA]["shortsignature"]]
                continue
            
            if token[Tokenizer.T_KIND] == "p":
                if "signature" in token[Tokenizer.T_EXTRA]:
                    token[Tokenizer.T_EXTRA]["status"]="Proto: $#" + token[Tokenizer.T_EXTRA]["signature"]
                else:
                    token[Tokenizer.T_EXTRA]["status"]= "Proto: $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t()", token[Tokenizer.T_NAME]+token[Tokenizer.T_EXTRA]["shortsignature"]]
                continue
            
            if token[Tokenizer.T_KIND] == "v":
                token[Tokenizer.T_EXTRA]["status"]="Global: " + CComplete.pretty_type(token[Tokenizer.T_SEARCH]) + " $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t"+CComplete.pretty_type(token[Tokenizer.T_SEARCH]), token[Tokenizer.T_NAME]]
                continue

            if token[Tokenizer.T_KIND] == "l":
                token[Tokenizer.T_EXTRA]["status"]="Local: " + CComplete.pretty_type(token[Tokenizer.T_SEARCH]) + " $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t"+CComplete.pretty_type(token[Tokenizer.T_SEARCH]), token[Tokenizer.T_NAME]]
                continue

            if token[Tokenizer.T_KIND] == "d":
                token[Tokenizer.T_EXTRA]["status"]="Macro: " + " ".join(token[Tokenizer.T_SEARCH][2:-2].strip().split())
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t#define", token[Tokenizer.T_NAME]]
                continue

            if token[Tokenizer.T_KIND] == "e":
                token[Tokenizer.T_EXTRA]["status"]="Enum: " + token[Tokenizer.T_EXTRA]["enum"] + " = {..., $#, ...}"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t" + token[Tokenizer.T_EXTRA]["enum"], token[Tokenizer.T_NAME]]
                continue

            if token[Tokenizer.T_KIND] == "s":
                token[Tokenizer.T_EXTRA]["status"]="Struct: $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\tstruct", token[Tokenizer.T_NAME]]
                continue

            if token[Tokenizer.T_KIND] == "c":
                token[Tokenizer.T_EXTRA]["status"]="Class: $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\tclass", token[Tokenizer.T_NAME]]
                continue

            if token[Tokenizer.T_KIND] == "t":
                if "typeref" in token[Tokenizer.T_EXTRA]:
                    token[Tokenizer.T_EXTRA]["status"]="Typedef: " + token[Tokenizer.T_EXTRA]["typeref"] + " $#"
                    token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t" + token[Tokenizer.T_EXTRA]["typeref"], token[Tokenizer.T_NAME]]
                else:
                    token[Tokenizer.T_EXTRA]["status"]="Typedef: $#"
                    token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\ttypedef", token[Tokenizer.T_NAME]]
                continue

            if token[Tokenizer.T_KIND] == "m":
                if "typeref" in token[Tokenizer.T_EXTRA]:
                    token[Tokenizer.T_EXTRA]["status"]="Member: " + token[Tokenizer.T_EXTRA]["typeref"] + " $#"
                    token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME].split("::")[-1]+"\t" + token[Tokenizer.T_EXTRA]["typeref"], token[Tokenizer.T_NAME].split("::")[-1]]
                else:
                    token[Tokenizer.T_EXTRA]["status"]="Member: " + CComplete.pretty_type(token[Tokenizer.T_SEARCH]) + " $#"
                    token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME].split("::")[-1]+"\t" + CComplete.pretty_type(token[Tokenizer.T_SEARCH]), token[Tokenizer.T_NAME].split("::")[-1]]
                continue

            if token[Tokenizer.T_KIND] == "u":
                token[Tokenizer.T_EXTRA]["status"]="Union: $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\tunion", token[Tokenizer.T_NAME]]
                continue

            if token[Tokenizer.T_KIND] == "a":
                type=token[Tokenizer.T_EXTRA]["type"]
                if token[Tokenizer.T_EXTRA]["pointer"]:
                    type="*"+type
                if "array" in token[Tokenizer.T_EXTRA]:
                    type=type+token[Tokenizer.T_EXTRA]["array"]
                token[Tokenizer.T_EXTRA]["status"]="Param: " + type + " $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t"+type, token[Tokenizer.T_NAME]]
                continue

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
            self.prettify(tokens)
            self.add_tokens(tokens)
            self.functiontokens[filename] = functokens
        self.sortedtokens = [x.lower() for x in self.tokens.keys()]
        self.sortedtokens.sort()
        rem = self.T.clean_cache()
        print("Removed %d entries" % rem)
        print("Done loading, %d files" % len(self.files))

    def search_tokens(self, prefix):
        prefix = prefix.lower()
        pos=bisect.bisect_left(self.sortedtokens, prefix)
        results=[]
        while pos < len(self.sortedtokens):
            if self.sortedtokens[pos].startswith(prefix):
                results.append(self.tags[self.taglist[pos]])
            else:
                break
            pos+=1
        return results
