from subprocess import PIPE, Popen
import os.path
import copy
import re
import linecache

class Tokenizer:
    T_NAME = 0
    T_FILENAME = 1
    T_SEARCH = 2
    T_LINE = 3
    T_KIND = 4
    T_EXTRA = 5

    K_FUNC = "f"
    K_PROTO = "p"
    K_LOCAL = "l"
    K_PARAM = "a"
    K_VARIABLE = "v"
    K_MACRO = "d"
    K_MEMBER = "m"
    # todo: complete list...

    declre = re.compile('(const\s)*(\w+)\s*([\s\*]?)\s*(\w+)(\[.*\])?')

    def __init__(self, cachesize = 500):
        self.cachesize = cachesize
        self.clear_cache()

    def clear_cache(self):
        linecache.clearcache()
        self.cache = {}
        self.cacheentries = []

    def cache_size(self):
        return len(self.cacheentries)

    def set_cache_size(self, newsize):
        self.cachesize = newsize

    def files_valid(self, files):
        for file in files:
            if file in self.cacheentries:
                date, _ = self.cache[file]
                if os.path.getmtime(file) > date:
                    return False
            else:
                return False
        return True

    def clean_cache(self, keepSet = [], modOnly = False):
        linecache.checkcache()
        remove = set([])
        i=0
        for file in self.cacheentries:
            date, _ = self.cache[file]
            if os.path.getmtime(file) > date or i>self.cachesize:
                remove.add(file)
                del self.cache[file]
            elif not modOnly:
                i+=1
        totrem = len(remove)
        if totrem > 0:
            newentries = []
            for e in self.cacheentries:
                if not e in remove:
                    newentries.append(e)
            self.cacheentries = newentries
        return totrem

    def scan_file(self, filename):
        if filename in self.cacheentries:
            self.cacheentries.remove(filename)
            self.cacheentries.insert(0, filename)
            _, values = self.cache[filename]
            return values

        time = os.path.getmtime(filename)
        tags = {}
        functiontags = {}

        attribs=["ctags", "-f-", "-u", "--excmd=pattern", "--c-kinds=+cdefglmnpstuv", "--fields=+naimSt", "--extra=+q"]
        attribs.append(filename)
        lastfuncid=""
        p = Popen(attribs, stdout=PIPE)
        while True:
            line = p.stdout.readline().decode('utf-8')
            if not line:
                break
            if line[0] == "!":
                continue
            parsed=Tokenizer.parse_line(line, filename)
            name=parsed[Tokenizer.T_NAME]
            if parsed[Tokenizer.T_KIND] == Tokenizer.K_MEMBER and name.find("::") == -1:
                continue
            if parsed[Tokenizer.T_KIND] == Tokenizer.K_MACRO and name.find("#define") == -1:
                continue
            if parsed[Tokenizer.T_KIND] == Tokenizer.K_LOCAL:
                if not lastfuncid in functiontags:
                    functiontags[lastfuncid] = []
                functiontags[lastfuncid].append(parsed)
            else:
                if parsed[Tokenizer.T_KIND] == Tokenizer.K_FUNC:
                    parsed[Tokenizer.T_EXTRA]["shortsignature"], functags = Tokenizer.parse_signature(parsed, filename)
                    lastfuncid=parsed[Tokenizer.T_NAME]
                    functiontags[lastfuncid] = functags
                elif parsed[Tokenizer.T_KIND] == Tokenizer.K_PROTO:
                    parsed[Tokenizer.T_EXTRA]["shortsignature"], _ = Tokenizer.parse_signature(parsed, filename)
                if name in tags:
                    tags[name] = Tokenizer.best_match([tags[name], parsed])
                else:
                    tags[name] = parsed
        self.cacheentries.insert(0, filename)
        self.cache[filename] = (time, (tags, functiontags))
        return (tags, functiontags)

    @staticmethod
    def best_match(options):
        scorestring="xpmfvald"
        highscore=-2
        best = None
        for option in options:
            score = scorestring.find(option[Tokenizer.T_KIND])
            if score > highscore:
                highscore = score
                best = option
        return best

    @staticmethod
    def parse_signature(parsed, filename):
        if not "signature" in parsed[Tokenizer.T_EXTRA]:
            return ("??", None)
        signature=parsed[Tokenizer.T_EXTRA]["signature"][1:-1]
        args=signature.split(",")
        ftags=[]
        short=[]

        i=1
        for arg in args:
            var = Tokenizer.parsevariable(arg)
            if var:
                extra = copy.deepcopy(parsed[Tokenizer.T_EXTRA])
                extra["type"] = var[1]
                extra["pointer"] = var[2]
                if var[3]:
                    extra["array"] = var[3]
                ftags.append((var[0], filename, arg, parsed[Tokenizer.T_LINE], Tokenizer.K_PARAM, extra))
                s=var[0]
                if var[2]:
                    s="*"+s
                if var[3]:
                    s=s+var[3]
                short.append("${"+str(i)+":"+s+"}")
                i+=1
        shortsign = "("+", ".join(short)+")"
        if parsed[Tokenizer.T_KIND] == "f":
            return (shortsign, ftags)
        return (shortsign, None)

    @staticmethod
    def parse_line(line, filename):
        line = line.rstrip()
        basic, extended = line.split(";\"\t",1)
        token, _, fsearch = basic.split("\t",2)
        ex_fields = extended.split("\t")
        type=ex_fields[0]
        exdict={}
        search = fsearch[2:-2]
        linenum = None
        for i in range(1,len(ex_fields)):
            name, value=ex_fields[i].split(":", 1)
            if name == "line":
                linenum = int(value)
            else:
                exdict[name] = value
        if type == Tokenizer.K_LOCAL or type == Tokenizer.K_VARIABLE:
            var = Tokenizer.parsevariable(search)
            if var:
                exdict["type"] = var[1]
                exdict["pointer"] = var[2]
                if var[3]:
                    exdict["array"] = var[3]
        if type == Tokenizer.K_MACRO and fsearch[-2:] != "$/":
            search = linecache.getline(filename, linenum)[0:-1]
        return (token, filename, search, linenum, type, exdict)

    @staticmethod
    def parsevariable(decl):
        decl=decl.strip()
        r = Tokenizer.declre.match(decl)
        if r:
            return (r.group(4), r.group(2), r.group(3) == "*", r.group(5))

