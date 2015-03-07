import sublime, sublime_plugin
import re, bisect, os.path
from subprocess import PIPE, Popen
import traceback, copy, linecache
#   "auto_complete_triggers": [ {"selector": "source.c++", "characters": ".>"} ]

T_NAME=0
T_FILENAME=1
T_SEARCH=2
T_LINE=3
T_KIND=4
T_EXTRA=5

class TagFileSearch():
    def __init__(self, basepath, filenames):
        try:
            self.tags = {}
            self.filetags = {}
            self.functiontags = {}
            attribs=["ctags", "-f-", "-u", "-R", "--c-kinds=+cdefglmnpstuvx", "--fields=+naimSt", "--extra=+q"]
            attribs.extend(filenames)
            lastfuncid=""
            p = Popen(attribs, stdout=PIPE, cwd=basepath)
            while True:
                line = p.stdout.readline().decode('utf-8')
                if not line:
                    break
                if line[0] == "!":
                    continue
                parsed=TagFileSearch.parse_line(line, basepath)
                name=parsed[T_NAME].lower()
                file=parsed[T_FILENAME]
                if parsed[T_KIND] == "l":
                    self.functiontags[lastfuncid].append(parsed)
                else:
                    if name in self.tags:
                        self.tags[name].append(parsed)
                    else:
                        self.tags[name] = [parsed]
                    if file in self.filetags:
                        self.filetags[file].append(parsed)
                    else:
                        self.filetags[file] = [parsed]
                    if parsed[T_KIND] == "f":
                        lastfuncid=parsed[T_FILENAME]+"@"+parsed[T_NAME]
                    if parsed[T_KIND] == "f" or parsed[T_KIND] == "p":
                        parsed[T_EXTRA]["shortsignature"] = self._parse_signature(parsed)                        
            self.taglist = list(self.tags.keys())
            self.taglist.sort()
            print("Read %d tags" % len(self.tags))
        except Exception as err:
            print(Exception)
            print(err)
            print(traceback.format_exc())
        linecache.clearcache()

    @staticmethod
    def parsevariable(decl):
        decl=decl.strip()
        r = re.match('(const\s)*(\w+)\s*([\s\*]?)\s*(\w+)(\[.*\])?', decl)
        if r:
            return (r.group(4), r.group(2), r.group(3) == "*", r.group(5))

    def _parse_signature(self, parsed):
        if "signature" in parsed[T_EXTRA]:
            signature=parsed[T_EXTRA]["signature"][1:-1]
            args=signature.split(",")
            funcid=parsed[T_FILENAME]+"@"+parsed[T_NAME]
            ftags=[]
            short=[]
            i=1
            for arg in args:
                var = TagFileSearch.parsevariable(arg)
                if var:
                    extra = copy.deepcopy(parsed[T_EXTRA])
                    extra["type"] = var[1]
                    extra["pointer"] = var[2]
                    if var[3]:
                        extra["array"] = var[3]
                    ftags.append((var[0], parsed[T_FILENAME], parsed[T_SEARCH], parsed[T_LINE], "a", extra))
                    s=var[0]
                    if var[2]:
                        s="*"+s
                    if var[3]:
                        s=s+var[3]
                    short.append("${"+str(i)+":"+s+"}")
                    i+=1
                # arg=arg.strip()
                # r = re.match('(\w+)\s*([\s\*]?)\s*(\w+)(\[.*\])?', arg)
                # if r:
                #     extra = copy.deepcopy(parsed[T_EXTRA])
                #     extra["type"] = r.group(1)
                #     extra["pointer"] = (r.group(2) == "*")
                #     if r.group(4):
                #         extra["array"] = r.group(4)
                #     ftags.append((r.group(3), parsed[T_FILENAME], parsed[T_SEARCH], parsed[T_LINE], "a", extra))
            if parsed[T_KIND] == "f":
                self.functiontags[funcid] = ftags
            return "("+", ".join(short)+")"

    @staticmethod
    def parse_line(line, basepath):
        line = line.rstrip()
        basic, extended = line.split(";\"\t",1)
        token, file, search = basic.split("\t",2)
        ex_fields = extended.split("\t")
        type=ex_fields[0]
        exdict={}
        if search[0] != "/" and search.isdecimal():
            fullpath = os.path.join(basepath, file)
            search = "/^"+linecache.getline(fullpath, int(search))+"$/"
        for i in range(1,len(ex_fields)):
            name, value=ex_fields[i].split(":", 1)
            exdict[name] = value
        return (token, file, search, int(exdict['line']), type, exdict)

    def get_tokens(self, tokenname):
        tokenname = tokenname.lower()
        if tokenname in self.tags:
            return self.tags[tokenname]
        else:
            return []

    def get_func_attribs(self, filename, functionname):
        if filename and functionname:
            id=filename+"@"+functionname
            if id in self.functiontags:
                return self.functiontags[id]
        return []

    def token_list(self):
        return self.taglist

    def search_tokens(self, prefix):
        prefix = prefix.lower()
        pos=bisect.bisect_left(self.taglist, prefix)
        results=[]
        while True:
            if self.taglist[pos].startswith(prefix):
                results.extend(self.tags[self.taglist[pos]])
            else:
                break
            pos+=1
        return results

    def get_file_tokens(self, filename):
        if filename in self.filetags:
            return self.filetags[filename]
        else:
            return []

    @staticmethod
    def find_includes(filename):
        includes = set([])
        if not os.path.isfile(filename):
            return includes
        with open(filename, 'r') as fp:
            for line in fp:
                line = line.lstrip();
                if line.startswith("#include"):
                    quoted = re.search('^\s*#include\s+"(.*)"', line)
                    if quoted:
                        includes.add(quoted.group(1));
        return includes

    @staticmethod
    def _makefullpath(basepaths, filename):
        for path in basepaths:
            if os.path.isfile(path+"/"+filename):
                return path+"/"+filename
        return None

    @staticmethod
    def find_recursive_includes(basepaths, filename):
        todo=[filename]
        done=[]

        while len(todo) > 0:
            progress = todo.pop(0)
            done.append(progress)
            progress = TagFileSearch._makefullpath(basepaths, progress)
            includes = TagFileSearch.find_includes(progress)
            for i in includes:
                if i not in todo and i not in done and TagFileSearch._makefullpath(basepaths, i):
                    todo.append(i)
        return done

active_ctags_listener = None
jump_history = []

class CTagsComplete(sublime_plugin.EventListener):
    def __init__(self):
        self.tfs = None
        self.ready = False
        self.files = []
        self.tokens = []
        self.loadedfile = None
        if sublime.active_window().active_view():
            self.reload(sublime.active_window().active_view().file_name())

    def getbasepath(self, filename):
        try:
            data = sublime.active_window().project_data()
            projectfolder = os.path.dirname(sublime.active_window().project_file_name())
            for folder in data["folders"]:
                path = os.path.join(projectfolder, folder["path"])
                if filename.startswith(path):
                    return path
            return None
        except:
            return None

    def set_status(self, text = None):
        view = sublime.active_window().active_view()
        if text is None or text == "":
            view.erase_status("ctcomplete")
        else:
            view.set_status("ctcomplete", text)

    def is_source_file(self, filename):
        for ext in ["c", "cpp", "cxx"]:
            if filename.endswith("." + ext):
                return True
        return False

    def is_header_file(self, filename):
        for ext in ["h", "hpp", "hxx"]:
            if filename.endswith("." + ext):
                return True
        return False

    def find_matching_source_file(self, basepath, filename):
        filename = os.path.join(basepath, filename)
        for ext in ["h", "hpp", "hxx"]:
            if filename.endswith("." + ext):
                filename = filename[0:-len(ext)]
                break
        for ext in ["c", "cpp", "cxx"]:
            if os.path.isfile(filename + ext):
                return filename + ext
        return None

    def reload(self, filename):
        global active_ctags_listener
        self.ready = False
        if filename:
            try:
                self.set_status("Loading tags...")
                self.loadedfile = filename
                print("Reloading...")
                self.basepath = self.getbasepath(filename)
                print("Reloading...A")
                filename = os.path.relpath(filename, self.basepath)
                print("Reloading...B")
                self.files = TagFileSearch.find_recursive_includes([self.basepath], filename)
                if self.is_header_file(filename):
                    source = self.find_matching_source_file(self.basepath, filename)
                    if source:
                        self.files.append(os.path.relpath(source, self.basepath))
                print("Reloading...C")
                print("basepath = %s" % self.basepath)
                print("files:")
                print(self.files)
                self.tfs = TagFileSearch(self.basepath, self.files)
                print("getting tokens")
                self.tokens = self.tfs.token_list()
                print("Done! (%d tokens)" % len(self.tokens))
                self.set_status("Tags loaded")
                active_ctags_listener = self
                self.ready = True
            except Exception as err:
                self.set_status("Error while loading tags")
                print("Error happened, no completions for you")
                print(Exception)
                print(err)
                print(traceback.format_exc())
                self.loadedfile = ""
                self.tfs = None
                self.files = []                
                self.tokens = []
                self.ready == False
        else:
            self.ready = False
            self.loadedfile = ""
            self.tfs = None
            self.files = []
            self.tokens = []

    def on_activated_async(self, view):
        print("on_activated_async")
        print("%s - %s" % (self.loadedfile, view.file_name()))
        if not view.file_name():
            return
        if self.loadedfile != view.file_name():
            self.reload(view.file_name())

    def on_post_save_async(self, view):
        self.reload(view.file_name())

    def on_load_async(self, view):
        self.reload(view.file_name()) #useless because on_activated ???

    @staticmethod
    def get_type(line):
        if line[0:2] == "/^" and line[-2:] == "$/":
            line = line[2:-2]
        return line.lstrip().split()[0]

    @staticmethod
    def pretty_type(line):
        if line[0:2] == "/^" and line[-2:] == "$/":
            line = line[2:-2]
        type = TagFileSearch.parsevariable(line)
        if not type:
            return line.lstrip().split()[0]
        ret=type[1]
        if type[2]:
            ret="*"+ret
        if type[3]:
            ret=ret+type[3]
        return ret

    def get_base_type(self, type):
        print("get_base_type: %s" % type)
        if type.lower() in self.tokens:
            tokens = self.tfs.get_tokens(type)
            for token in tokens:
                if token[T_KIND] == "t" or token[T_KIND] == "m":
                    if "typeref" in token[T_EXTRA]:
                        ref=token[T_EXTRA]['typeref']
                        if ref.startswith("struct:") or ref.startswith("union:"):
                            ref = ref.split(":",1)[1]
                        print("ref: %s" % ref)
                        if ref == type:
                            print("inf. recurse")
                            return type
                        return self.get_base_type(ref)
                    else:
                        print("no typeref")
                        ref = CTagsComplete.get_type(token[T_SEARCH])
                        return self.get_base_type(ref)
        print("No token: %s" % type)
        return type

    def make_completions(self, results):
        completions = []
        for result in results:
            print(result)
            if result[T_KIND] == "v" or result[T_KIND] == "l":
                completions.append([result[T_NAME]+"\t"+CTagsComplete.pretty_type(result[T_SEARCH]), result[T_NAME]])
                continue;
            if result[T_KIND] == "d":
                completions.append([result[T_NAME]+"\t#define", result[T_NAME]])
                continue;
            if result[T_KIND] == "e":
                completions.append([result[T_NAME]+"\t" + result[T_EXTRA]["enum"], result[T_NAME]])
                continue;
            if result[T_KIND] == "f" or result[T_KIND] == "p":
                completions.append([result[T_NAME]+"\t()", result[T_NAME]+result[T_EXTRA]["shortsignature"]])
                continue;
            if result[T_KIND] == "s" or result[T_KIND] == "c":
                completions.append([result[T_NAME]+"\tstruct", result[T_NAME]])
                continue;
            if result[T_KIND] == "t":
                if "typeref" in result[T_EXTRA]:
                    completions.append([result[T_NAME]+"\t" + result[T_EXTRA]["typeref"], result[T_NAME]])
                else:
                    completions.append([result[T_NAME]+"\ttypedef", result[T_NAME]])
                continue;
            if result[T_KIND] == "m":
                if "typeref" in result[T_EXTRA]:
                    completions.append([result[T_NAME].split("::")[-1]+"\t" + result[T_EXTRA]["typeref"], result[T_NAME].split("::")[-1]])
                else:
                    completions.append([result[T_NAME].split("::")[-1]+"\t" + CTagsComplete.pretty_type(result[T_SEARCH]), result[T_NAME].split("::")[-1]])
                continue;
            if result[T_KIND] == "u":
                completions.append([result[T_NAME]+"\tunion", result[T_NAME]])
            if result[T_KIND] == "a":
                type=result[T_EXTRA]["type"]
                if result[T_EXTRA]["pointer"]:
                    type="*"+type
                if "array" in result[T_EXTRA]:
                    type=type+result[T_EXTRA]["array"]
                completions.append([result[T_NAME]+"\t"+type, result[T_NAME]])
        return (completions, sublime.INHIBIT_WORD_COMPLETIONS)

    def make_rel_filename(self, filename):
        filename = os.path.relpath(filename, self.basepath)
        return filename

    def get_member_completions(self, view, search, pos, filename):
        # pos = locations[0]
        line = view.line(pos)
        line.b=pos
        line=view.substr(line)
        line = re.split(',|;|\(|\s+', line.strip())[-1].strip()
        chain = [x.split("[", 1)[0] for x in re.split('->|\.|::', line.strip())]
        print(chain)
        tokens = [x for x in self.tfs.get_func_attribs(filename, self.get_func_name(view)) if x[T_NAME] == chain[0]]
        tokens.extend([x for x in self.tfs.get_tokens(chain[0]) if x[T_KIND]=="v"])
        if chain[0] in self.tokens or len(tokens)>0:
            # tokens.extend(self.tfs.get_tokens(chain[0]))
            goodtokens = [x for x in tokens if x[T_KIND] == "v" or (x[T_KIND] == "l" and x[T_FILENAME] == filename) or (x[T_KIND] == "a")]
            print("goodtokens")
            print(goodtokens)
            if len(goodtokens) > 0:
                #todo, insert sorting here
                token = goodtokens[0]
                print(token)
                type=""
                if token[T_KIND] == "a":
                    type = token[T_EXTRA]["type"]
                else:
                    type = CTagsComplete.get_type(token[T_SEARCH])
                print(type)
                type = self.get_base_type(type)
                print(type)
                for newtype in chain[1:-1]:
                    type = type + "::" + newtype
                    print(type)
                    type = self.get_base_type(type)
                    print(type)
                    print("---")
                print(type)
                members = self.tfs.search_tokens(type + "::")
                goodmembers = [x for x in members if x[T_NAME][len(type)+2:].find("::") == -1]
                print(goodmembers)
                return goodmembers

    def on_query_completions(self, view, search, locations):
        if not view.file_name() or self.ready == False:
            return None
        filename = os.path.relpath(view.file_name(), self.basepath)
        i=locations[0]-len(search)
        print("No prefix: %d" % i)
        prevword=view.substr(view.word(i))
        print(prevword)
        if i>2 and (view.substr(sublime.Region(i-2, i)) == "->" or view.substr(sublime.Region(i-1, i)) == "." or view.substr(sublime.Region(i-2, i)) == "::"):
            return self.make_completions(self.get_member_completions(view, search, i, filename))
        validtokens = [x for x in self.tokens if x.startswith(search.lower())]
        fulltokens = []
        if self.get_func_name(view):
            fulltokens.extend(self.tfs.get_func_attribs(filename, self.get_func_name(view)))

        for token in validtokens:
            t=self.tfs.get_tokens(token)
            tok = [x for x in t if x[T_KIND] != "m"]
            fulltokens.extend(tok)

        return self.make_completions(fulltokens)

    def get_func_name(self, view):
        sel = view.sel()[0]
        functionRegs = view.find_by_selector('meta.function.c')
        func = "";
        for r in reversed(functionRegs):
            if r.a <= sel.a and r.b >= sel.a:
                funcname=view.substr(sublime.Region(r.a, view.line(r.a).b)).lstrip()
                funcname=funcname.split("(",1)[0]
                return funcname

    def show_pretty_status(self, result):
        if result:
            word=result[T_NAME]
            if result[T_KIND] == "f":
                return ("Func: " + word+result[T_EXTRA]["signature"])
            
            if result[T_KIND] == "p":
                if "signature" in result[T_EXTRA]:
                    return ("Proto: " + word+result[T_EXTRA]["signature"])
                return ("Proto: " + word)
            
            if result[T_KIND] == "v":
                return ("Global: " + CTagsComplete.pretty_type(result[T_SEARCH]) + " " + word)

            if result[T_KIND] == "l":
                return ("Local: " + CTagsComplete.pretty_type(result[T_SEARCH]) + " " + word)

            if result[T_KIND] == "d":
                return ("Macro: " + " ".join(result[T_SEARCH][2:-2].strip().split()))

            if result[T_KIND] == "e":
                return ("Enum: " + result[T_EXTRA]["enum"] + " = {..., " + word + ", ...}")

            if result[T_KIND] == "s":
                return ("Struct: " + word)

            if result[T_KIND] == "c":
                return ("Class: " + word)

            if result[T_KIND] == "t":
                if "typeref" in result[T_EXTRA]:
                    return ("Typedef: " + result[T_EXTRA]["typeref"] + " " + word)
                else:
                    return ("Typedef: " + word)

            if result[T_KIND] == "m":
                if "typeref" in result[T_EXTRA]:
                    return ("Member: " + result[T_EXTRA]["typeref"] + " " + word)
                else:
                    return ("Member: " + CTagsComplete.pretty_type(result[T_SEARCH]) + " " + word)

            if result[T_KIND] == "u":
                return ("Union: " + word)

            if result[T_KIND] == "a":
                type=result[T_EXTRA]["type"]
                if result[T_EXTRA]["pointer"]:
                    type="*"+type
                if "array" in result[T_EXTRA]:
                    type=type+result[T_EXTRA]["array"]
                return ("Param: " + type + " " + word)
        return ""

    def get_best_match(self, options):
        best=None
        bestscore=-2
        scorestring="pmfval"
        for option in options:
            print(option)
            score = scorestring.find(option[T_KIND])
            if score > bestscore:
                bestscore = score
                best = option
        return best

    def get_sel_token(self, view):
        if not view.file_name() or self.ready == False:
            return
        selword = view.word(view.sel()[0].end())
        i = selword.begin()
        word = view.substr(selword)
        filename = self.make_rel_filename(view.file_name())
        if i>2 and (view.substr(sublime.Region(i-2, i)) == "->" or view.substr(sublime.Region(i-1, i)) == "." or view.substr(sublime.Region(i-2, i)) == "::"):
            print("Got here: " + word)
            members = self.get_member_completions(view, word, i, filename)
            for m in members:
                if m[T_NAME].endswith("::" + word):
                    return m
            return

        func = [x for x in self.tfs.get_func_attribs(filename, self.get_func_name(view)) if x[T_NAME] == word]
        result = None
        if len(func) > 0:
            return self.get_best_match(func)
        alltokens = self.tfs.get_tokens(word)
        if len(alltokens) > 0:
            return self.get_best_match(alltokens)

    def show_number(self, word):
        num=None
        try:
            if word[0:2] == "0x":
                num=int(word, 16)
            elif word[0:1] == "0":
                num=int(word, 8)
            else:
                num=int(word)
            self.set_status("Integer: HEX=0x%s DEC=%s OCT=%s" % (format(num, "X"), int(num), format(num, "#o")))
        except:
            self.set_status()

    def on_selection_modified_async(self, view):
        token = self.get_sel_token(view)
        if token:
            self.set_status(self.show_pretty_status(token))
        else:
            selword = view.word(view.sel()[0].end())
            word = view.substr(selword)
            self.show_number(word)

    def jump_back(self):
        if len(jump_history):
            pos = jump_history.pop()
            sublime.active_window().open_file(pos, sublime.ENCODED_POSITION)

    def jump_token(self, token, word="", preview = False):
        print("Jumping to")
        print(token)
        file = self.basepath + "/" + token[T_FILENAME]
        line = token[T_LINE]
        print("file")
        print(file)
        print("line")
        print(line)
        offset=""
        if token[T_SEARCH][0] == "/" and token[T_SEARCH].find(word) != -1:
            offset = ":" + str(token[T_SEARCH].find(word)-1+len(word))
            print("offset")
            print(offset)
        print(file+":"+str(line)+offset)
        view = sublime.active_window().active_view()
        if view.file_name() and not preview:
            pos = view.sel()[0].end()
            row, col = view.rowcol(pos)
            loc = view.file_name() + ":" + str(row+1) + ":" + str(col)
            jump_history.append(loc)
            print(jump_history)
        flags = sublime.ENCODED_POSITION
        if preview:
            flags = flags | sublime.TRANSIENT
        sublime.active_window().open_file(file+":"+str(line)+offset, flags)

class ctags_jump_definition(sublime_plugin.TextCommand):
    def run(self, edit):
        global active_ctags_listener
        view = sublime.active_window().active_view()

        selword = view.word(view.sel()[0].end())
        word = view.substr(selword)

        token = active_ctags_listener.get_sel_token(view)
        if token:
            active_ctags_listener.jump_token(token, word)

class ctags_jump_back(sublime_plugin.TextCommand):
    def run(self, edit):
        global active_ctags_listener
        active_ctags_listener.jump_back()

class ctags_show_symbols(sublime_plugin.TextCommand):
    def run(self, edit):
        global active_ctags_listener
        view = sublime.active_window().active_view()
        # sel=[]
        # for s in view.sel():
        #     sel.append(s)
        filename = os.path.relpath(view.file_name(), active_ctags_listener.basepath)
        tokens = active_ctags_listener.tfs.get_func_attribs(filename, active_ctags_listener.get_func_name(view))
        for token in active_ctags_listener.tokens:
            tokens.extend(active_ctags_listener.tfs.get_tokens(token))

        # def on_select(i):
        #     if i == -1:
        #         return
        #     token = tokens[i]
        #     active_ctags_listener.jump_token(token, token[T_NAME], True)

        def on_done(i):
            if i == -1:
                # view.sel().clear()
                # view.sel().add_all(sel)
                # view.show_at_center(sel[0])
                return
            token = tokens[i]
            active_ctags_listener.jump_token(token, token[T_NAME])

        # tokenlist = []
        # for x in tokens:
        #     print(active_ctags_listener.show_pretty_status(x))
        #     tokenlist.append([[x[T_NAME], active_ctags_listener.show_pretty_status(x)]])
        tokenlist = [[x[T_NAME], active_ctags_listener.show_pretty_status(x)] for x in tokens]
        sublime.active_window().show_quick_panel(tokenlist, on_done, 0, 0) #, on_select)
