import sublime, sublime_plugin
import os, re
from CComplete.ccomplete import CComplete
from CComplete.tokenizer import Tokenizer

CCP = None

class CCompletePlugin(sublime_plugin.EventListener):
    def __init__(self):
        global CCP
        if CCP is None:
            CCP = self
        else:
            print("ERROR")
            return
        self.ready = False
        self.init = False

    def plugin_loaded(self):
        print("Plugin loaded!")
        self.settings = sublime.load_settings("ccomplete")
        cachepath = sublime.cache_path() + "/ccomplete_cache"
        if not os.path.exists(cachepath):
            os.mkdir(cachepath)
        self.cc = CComplete(self.settings.get('cache', 500), cachepath)
        self.currentfile = None
        self.ready = False
        self.extensions = self.settings.get("extensions", ["c", "cpp", "cxx", "h", "hpp", "hxx"])
        self.load_matching = self.settings.get("load_matching", True)
        self.init = True

    @staticmethod
    def showprogress(view, i, total):
        view.set_status("ctcomplete", "Loading completions (%d/%d)..." % (i, total))

    def load(self, view):
        if self.init == False:
            self.plugin_loaded()
        filename = view.file_name()
        view.erase_status("ctcomplete")
        self.ready = False
        if not filename:
            return
        loadOk = False
        base = ""
        for ext in self.extensions:
            if filename.endswith("." + ext):
                base = filename[0:-len(ext)]
                loadOk = True
                break
        if not loadOk:
            return

        extra = []
        if self.load_matching:
            for ext in self.extensions:
                if filename.endswith(ext):
                    continue
                if os.path.isfile(base + ext):
                    extra.append(base + ext)

        basepaths, syspaths = self.getProjectPaths(filename)
        if self.currentfile == filename and self.cc.is_valid(filename, basepaths, syspaths, extra):
            print("Valid")
            self.ready = True
            return
        print("Loading")
        view.set_status("ctcomplete", "Loading completions...")
        self.cc.load_file(filename, basepaths, syspaths, extra, lambda a, b: CCompletePlugin.showprogress(view, a, b))
        view.erase_status("ctcomplete")
        self.currentfile = filename
        self.ready = True

    def getProjectPaths(self, filename):
        # No valid filename
        if not filename or not os.path.isfile(filename):
            return ([], [])

        folders = []
        projectfolder = os.path.dirname(sublime.active_window().project_file_name())
        data = sublime.active_window().project_data()
        for folder in data["folders"]:
            path = os.path.join(projectfolder, folder["path"])
            folders.append(path)
        return (folders, [])

    def current_function(self, view):
        sel = view.sel()[0]
        functions = view.find_by_selector('meta.function.c')
        func = "";
        for f in functions:
            if f.contains(sel.a):
                funcname=view.substr(sublime.Region(f.a, view.line(f.a).b))
                funcname=funcname.split("(",1)[0]
                return funcname.strip()

    @staticmethod
    def get_type(line):
        return line.lstrip().split()[0]

    def get_base_type(self, type):
        type = type.lower()
        if type in self.cc.tokens:
            token = self.cc.tokens[type]
            if token[Tokenizer.T_KIND] == "t" or token[Tokenizer.T_KIND] == "m":
                if "typeref" in token[Tokenizer.T_EXTRA]:
                    ref=token[Tokenizer.T_EXTRA]['typeref']
                    if ref.startswith("struct:") or ref.startswith("union:"):
                        ref = ref.split(":",1)[1]
                    if ref == type:
                        return type
                    return self.get_base_type(ref)
                else:
                    ref = CCompletePlugin.get_type(token[Tokenizer.T_SEARCH])
                    return self.get_base_type(ref)
        return type

    def traverse_members(self, view, pos, full = False):
        filename = self.currentfile
        line = view.line(pos)
        line.b=pos
        line=view.substr(line)
        oldline=""
        while oldline != line:
            oldline = line
            line = re.sub(r'\[[^\[]*\]', '', line)
            print(line)
        line = re.split(',|;|\(|\[|\s+', line.strip())[-1].strip()
        print(line)
        chain = [x.split("[", 1)[0] for x in re.split('->|\.|::', line.strip())]
        print(chain)
        func = self.current_function(view)
        if not filename in self.cc.functiontokens or not func in self.cc.functiontokens[filename]:
            print("Not in a filled function (%s, %s)" % (filename, func))
            return []
        tokens = [x for x in self.cc.functiontokens[filename][func] if x[Tokenizer.T_NAME] == chain[0]]
        token = None
        if len(tokens) > 0:
            token = tokens[0]
        else:
            token = self.cc.tokens[chain[0].lower()]
            if not token or token[Tokenizer.T_KIND] != Tokenizer.K_VARIABLE:
                return []
        type=""
        if token[Tokenizer.T_KIND] == Tokenizer.K_PARAM:
            type = token[Tokenizer.T_EXTRA]["type"]
        else:
            type = Tokenizer.parsevariable(token[Tokenizer.T_SEARCH])[1]
        type = self.get_base_type(type)
        pchain = chain[1:]
        if not full:
            pchain = pchain[0:-1]
        for newtype in pchain:
            type = type + "::" + newtype
            type = self.get_base_type(type)
        members = self.cc.search_tokens(type + "::")
        goodmembers = [x for x in members if x[Tokenizer.T_NAME][len(type)+2:].find("::") == -1]
        return goodmembers

    def get_sel_token(self, view):
        if len(view.sel()) < 1:
            return None
        selword = view.word(view.sel()[0].end())
        i = selword.begin()
        word = view.substr(selword)
        if i>2 and (view.substr(sublime.Region(i-2, i)) == "->" or view.substr(sublime.Region(i-1, i)) == "." or view.substr(sublime.Region(i-2, i)) == "::"):
            members = self.traverse_members(view, selword.end())
            for m in members:
                if m[Tokenizer.T_NAME].endswith("::" + word):
                    return m
            return None

        func =  self.current_function(view)
        filename = self.currentfile
        if filename in self.cc.functiontokens and func in self.cc.functiontokens[filename] and self.cc.functiontokens[filename][func]:
            tokens = [x for x in self.cc.functiontokens[filename][func] if x[Tokenizer.T_NAME] == word]
            if len(tokens) > 0:
                return Tokenizer.best_match(tokens)
        if word.lower() in self.cc.tokens:
            return self.cc.tokens[word.lower()]
        return None

    def on_activated_async(self, view):
        self.load(view)

    def on_post_save_async(self, view):
        self.load(view)

    def on_query_completions(self, view, search, locations):
        if not self.ready:
            return

        i=locations[0]-len(search)
        if i>2 and (view.substr(sublime.Region(i-2, i)) == "->" or view.substr(sublime.Region(i-1, i)) == "." or view.substr(sublime.Region(i-2, i)) == "::"):
            members = self.traverse_members(view, locations[0])
            completions = [i[Tokenizer.T_EXTRA]["completion"] for i in members]
            return (completions, sublime.INHIBIT_WORD_COMPLETIONS)

        validtokens = [x for x in self.cc.search_tokens(search)]
        completions = []
        func = self.current_function(view)
        if func:
            completions.extend([x[Tokenizer.T_EXTRA]["completion"] for x in self.cc.functiontokens[self.currentfile][func]])

        completions.extend([x[Tokenizer.T_EXTRA]["completion"] for x in validtokens if x[Tokenizer.T_KIND] != Tokenizer.K_MEMBER])

        return (completions, sublime.INHIBIT_WORD_COMPLETIONS)

    def show_number(self, view):
        selword = view.word(view.sel()[0].end())
        word = view.substr(selword)
        num=None
        try:
            if word[0:2] == "0x":
                num=int(word, 16)
            elif word[0:1] == "0":
                num=int(word, 8)
            else:
                num=int(word)
            view.set_status("ctcomplete", "Integer: HEX=0x%s DEC=%s OCT=%s" % (format(num, "X"), int(num), format(num, "#o")))
        except:
            view.erase_status("ctcomplete")

    def on_selection_modified_async(self, view):
        if not self.ready:
            return

        token = self.get_sel_token(view)
        if token:
            selword = view.word(view.sel()[0].end())
            word = view.substr(selword)
            view.set_status("ctcomplete", token[Tokenizer.T_EXTRA]["status"].replace("$#", word))
        else:
            self.show_number(view)

    def jump_token_definition(self, token, word = None):
        offset = 0
        if word and token[Tokenizer.T_SEARCH].find(word) != -1:
            offset = token[Tokenizer.T_SEARCH].find(word)+len(word)+1
        flags = sublime.ENCODED_POSITION
        line = token[Tokenizer.T_LINE]
        file = token[Tokenizer.T_FILENAME]
        sublime.active_window().open_file(file+":"+str(line)+":"+str(offset), flags)

class ccomplete_jump_definition(sublime_plugin.TextCommand):
    def run(self, edit):
        global CCP
        if not CCP.ready:
            return
        view = sublime.active_window().active_view()

        selword = view.word(view.sel()[0].end())
        word = view.substr(selword)

        token=CCP.get_sel_token(view)
        CCP.jump_token_definition(token, word)

class ccomplete_show_symbols(sublime_plugin.TextCommand):
    def run(self, edit):
        global CCP
        if not CCP.ready:
            return
        global active_ctags_listener
        view = sublime.active_window().active_view()

        filename = CCP.currentfile
        func = CCP.current_function(view)

        tokens = []
        if func in CCP.cc.functiontokens[filename]:
            tokens.extend(CCP.cc.functiontokens[filename][func])
        tokens.extend(CCP.cc.tokens.values())

        def on_done(i):
            if i == -1:
                return
            token = tokens[i]
            CCP.jump_token_definition(token, token[Tokenizer.T_NAME])

        tokenlist = [[x[Tokenizer.T_NAME], x[Tokenizer.T_FILENAME] + ":" + str(x[Tokenizer.T_LINE])] for x in tokens]
        sublime.active_window().show_quick_panel(tokenlist, on_done, 0, 0)