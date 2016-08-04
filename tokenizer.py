from subprocess import PIPE, Popen
import os.path
import copy
import re
import marshal
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
    K_STRUCT = "s"
    K_UNION = "u"
    K_MEMBER = "m"
    # todo: complete list...

    declre = re.compile('(const\s)*(struct\s|union\s)*(\w+)\s*([\s\*])\s*(\w+)(\[.*\])?')

    def __init__(self, cachepath = "/tmp", cachesize = 500):
        self.cachesize = cachesize
        self.clear_cache()
        self.cachepath = cachepath

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
            if (not os.path.exists(file)) or os.path.getmtime(file) > date or i>self.cachesize:
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
            if filename in self.cache:
                self.cacheentries.insert(0, filename)
                _, values = self.cache[filename]
                return values

        hashfn = self.cachepath + "/" + str(hash(filename)) + ".ccache"
        time = os.path.getmtime(filename)

        if os.path.isfile(hashfn) and os.path.getmtime(hashfn) > os.path.getmtime(filename):
            with open(hashfn, 'rb') as f:
                values = marshal.load(f)
            self.cacheentries.insert(0, filename)
            self.cache[filename] = (time, values)
            return values

        tags = {}
        functiontags = {}

        attribs=["ctags", "-f-", "-u", "--excmd=pattern", "--c-kinds=+cdefglmnpstuv", "--fields=+naimSt", "--extra=+q"]
        attribs.append(filename)
        lastfuncid=""
        p = Popen(attribs, stdout=PIPE)
        while True:
            line = p.stdout.readline().decode('utf-8', errors='ignore')
            if not line:
                break
            if line[0] == "!":
                continue
            parsed=Tokenizer.parse_line(line, filename)
            name=parsed[Tokenizer.T_NAME]
            if parsed[Tokenizer.T_KIND] == Tokenizer.K_STRUCT and 'struct' in parsed[Tokenizer.T_EXTRA]:
                continue
            if parsed[Tokenizer.T_KIND] == Tokenizer.K_UNION and 'union' in parsed[Tokenizer.T_EXTRA]:
                continue
            if parsed[Tokenizer.T_KIND] == Tokenizer.K_MEMBER and name.find("::") == -1:
                continue
            if parsed[Tokenizer.T_KIND] == Tokenizer.K_MACRO and parsed[Tokenizer.T_SEARCH].find("#define") == -1:
                continue
            if parsed[Tokenizer.T_KIND] == Tokenizer.K_LOCAL:
                if not lastfuncid in functiontags:
                    functiontags[lastfuncid] = []
                Tokenizer.prettify(parsed)
                functiontags[lastfuncid].append(parsed)
            else:
                if parsed[Tokenizer.T_KIND] == Tokenizer.K_FUNC:
                    parsed[Tokenizer.T_EXTRA]["shortsignature"], functags = Tokenizer.parse_signature(parsed, filename)
                    lastfuncid=parsed[Tokenizer.T_NAME]
                    functiontags[lastfuncid] = functags
                elif parsed[Tokenizer.T_KIND] == Tokenizer.K_PROTO:
                    parsed[Tokenizer.T_EXTRA]["shortsignature"], _ = Tokenizer.parse_signature(parsed, filename)
                Tokenizer.prettify(parsed)
                if name in tags:
                    tags[name] = Tokenizer.best_match([tags[name], parsed])
                else:
                    tags[name] = parsed
        self.cacheentries.insert(0, filename)
        self.cache[filename] = (time, (tags, functiontags))
        with open(hashfn, 'wb') as f:
            marshal.dump((tags, functiontags), f)
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
            parsed[Tokenizer.T_EXTRA]["signature"] = "()"
            return ("()", [])
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
                p = (var[0], filename, parsed[Tokenizer.T_SEARCH], parsed[Tokenizer.T_LINE], Tokenizer.K_PARAM, extra)
                Tokenizer.prettify(p)
                ftags.append(p)
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
        token, _, search = basic.split("\t",2)
        ex_fields = extended.split("\t")
        type=ex_fields[0]
        exdict={}
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
        if search[0:2] == "/^" and search[-2:] == "$/":
            search = search[2:-2]
        elif search[0:2] == "/^" and search[-2:] == "(/":
            start=len(search)-3
            search = linecache.getline(filename, linenum)
            end=search.find(")", start)
            if end>0:
                sign=search[start:end]
                args = sign.split(",")
                newargs = []
                i=1
                for arg in args:
                    newargs.append("${" + str(i) + ":" + arg.strip() + "}")
                    i+=1
                exdict["shortsignature"] = "(" + ", ".join(newargs) + ")"
        else:
            search = linecache.getline(filename, linenum)
        hashr = "__anon" + str(hash(filename)) + "_"
        token = token.replace("__anon", hashr)
        if 'struct' in exdict:
            exdict['struct'] = exdict['struct'].replace("__anon", hashr)
        if 'union' in exdict:
            exdict['union'] = exdict['union'].replace("__anon", hashr)
        if 'typeref' in exdict:
            exdict['typeref'] = exdict['typeref'].replace("__anon", hashr)
        return (token, filename, search, linenum, type, exdict)

    @staticmethod
    def parsevariable(decl):
        decl=decl.strip()
        r = Tokenizer.declre.match(decl)
        if r:
            return (r.group(5), r.group(3), r.group(3) == "*", r.group(6))

    @staticmethod
    def pretty_type(line):
        if line[0:2] == "/^" and line[-2:] == "$/":
            print("OBSOLETE")
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

    @staticmethod
    def prettify(token):
        if token[Tokenizer.T_KIND] == "f":
            token[Tokenizer.T_EXTRA]["status"]="Func: $#" + token[Tokenizer.T_EXTRA]["signature"]
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t()", token[Tokenizer.T_NAME]+token[Tokenizer.T_EXTRA]["shortsignature"]]
            return
        
        if token[Tokenizer.T_KIND] == "p":
            if "signature" in token[Tokenizer.T_EXTRA]:
                token[Tokenizer.T_EXTRA]["status"]="Proto: $#" + token[Tokenizer.T_EXTRA]["signature"]
            else:
                token[Tokenizer.T_EXTRA]["status"]= "Proto: $#"
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t()", token[Tokenizer.T_NAME]+token[Tokenizer.T_EXTRA]["shortsignature"]]
            return
        
        if token[Tokenizer.T_KIND] == "v":
            token[Tokenizer.T_EXTRA]["status"]="Global: " + Tokenizer.pretty_type(token[Tokenizer.T_SEARCH]) + " $#"
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t"+Tokenizer.pretty_type(token[Tokenizer.T_SEARCH]), token[Tokenizer.T_NAME]]
            return

        if token[Tokenizer.T_KIND] == "d":
            token[Tokenizer.T_EXTRA]["status"]="Macro: " + " ".join(token[Tokenizer.T_SEARCH].strip().split())
            if "shortsignature" in token[Tokenizer.T_EXTRA]:
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t#define", token[Tokenizer.T_NAME] + token[Tokenizer.T_EXTRA]["shortsignature"]]
            else:
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t#define", token[Tokenizer.T_NAME]]
            return

        if token[Tokenizer.T_KIND] == "e":
            token[Tokenizer.T_EXTRA]["status"]="Enum: " + token[Tokenizer.T_EXTRA]["enum"] + " = {..., $#, ...}"
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t" + token[Tokenizer.T_EXTRA]["enum"], token[Tokenizer.T_NAME]]
            return

        if token[Tokenizer.T_KIND] == "s":
            token[Tokenizer.T_EXTRA]["status"]="Struct: $#"
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\tstruct", token[Tokenizer.T_NAME]]
            return

        if token[Tokenizer.T_KIND] == "c":
            token[Tokenizer.T_EXTRA]["status"]="Class: $#"
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\tclass", token[Tokenizer.T_NAME]]
            return

        if token[Tokenizer.T_KIND] == "t":
            if "typeref" in token[Tokenizer.T_EXTRA]:
                token[Tokenizer.T_EXTRA]["status"]="Typedef: " + token[Tokenizer.T_EXTRA]["typeref"] + " $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t" + token[Tokenizer.T_EXTRA]["typeref"], token[Tokenizer.T_NAME]]
            else:
                token[Tokenizer.T_EXTRA]["status"]="Typedef: $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\ttypedef", token[Tokenizer.T_NAME]]
            return

        if token[Tokenizer.T_KIND] == "m":
            if "typeref" in token[Tokenizer.T_EXTRA]:
                token[Tokenizer.T_EXTRA]["status"]="Member: " + token[Tokenizer.T_EXTRA]["typeref"] + " $#"
                cleantyperef = token[Tokenizer.T_EXTRA]["typeref"].split(":")[-1]
                if cleantyperef[0:6] == '__anon':
                    cleantyperef = "(Anonymous)"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME].split("::")[-1]+"\t" + cleantyperef, token[Tokenizer.T_NAME].split("::")[-1]]
            else:
                token[Tokenizer.T_EXTRA]["status"]="Member: " + Tokenizer.pretty_type(token[Tokenizer.T_SEARCH]) + " $#"
                token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME].split("::")[-1]+"\t" + Tokenizer.pretty_type(token[Tokenizer.T_SEARCH]), token[Tokenizer.T_NAME].split("::")[-1]]
            return

        if token[Tokenizer.T_KIND] == "u":
            token[Tokenizer.T_EXTRA]["status"]="Union: $#"
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\tunion", token[Tokenizer.T_NAME]]
            return

        if token[Tokenizer.T_KIND] == "l":
            token[Tokenizer.T_EXTRA]["status"]="Local: " + Tokenizer.pretty_type(token[Tokenizer.T_SEARCH]) + " $#"
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t"+Tokenizer.pretty_type(token[Tokenizer.T_SEARCH]), token[Tokenizer.T_NAME]]
            return

        if token[Tokenizer.T_KIND] == "a":
            type=token[Tokenizer.T_EXTRA]["type"]
            if token[Tokenizer.T_EXTRA]["pointer"]:
                type="*"+type
            if "array" in token[Tokenizer.T_EXTRA]:
                type=type+token[Tokenizer.T_EXTRA]["array"]
            token[Tokenizer.T_EXTRA]["status"]="Param: " + type + " $#"
            token[Tokenizer.T_EXTRA]["completion"]=[token[Tokenizer.T_NAME]+"\t"+type, token[Tokenizer.T_NAME]]
            return
