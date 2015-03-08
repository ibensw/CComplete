import sublime, sublime_plugin
import os.path
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
        self.cc = CComplete(500)
        self.currentfile = None
        self.cc.load_file("/home/ibensw/linux-4.0-rc2/include/linux/tcp.h", [], ["/home/ibensw/linux-4.0-rc2/include"])

    def getProjectPaths(self):
        # No valid filename
        if not filename or not os.path.isfile(filename):
            return ([], [])

        folders = []
        projectfolder = os.path.dirname(projectfile)
        data = sublime.active_window().project_data()
        for folder in data["folders"]:
            path = os.path.join(projectfolder, folder["path"])
            folders.append(path)
        return (folders, [])

    def current_function(view):
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
                    ref = CCompletePlugin.get_type(token[T_SEARCH])
                    return self.get_base_type(ref)
        return type

    def traverse_members(self, view, pos):
        filename = view.file_name()
        line = view.line(pos)
        line.b=pos
        line=view.substr(line)
        line = re.split(',|;|\(|\s+', line.strip())[-1].strip()
        chain = [x.split("[", 1)[0] for x in re.split('->|\.|::', line.strip())]
        print(chain)
        func = self.current_function(view)
        if not filename in self.cc.functiontokens or not func in self.cc.functiontokens[filename]:
            return None
        tokens = [x for x in self.cc.functiontokens[filename][func] if x[Tokenizer.T_NAME] == chain[0]]
        if len(tokens) == 0:
            tokens = [x for x in self.cc.tokens(chain[0].lower()) if x[Tokenizer.T_KIND]=="v"]
        if len(tokens) == 0:
            return
        token = tokens[0]
        type=""
        if token[Tokenizer.T_KIND] == Tokenizer.K_PARAM:
            type = token[Tokenizer.T_EXTRA]["type"]
        else:
            type = Tokenizer.parsevariable(token[Tokenizer.T_SEARCH])[1]
        type = self.get_base_type(type)
        for newtype in chain[1:-1]:
            type = type + "::" + newtype
            type = self.get_base_type(type)
        members = self.tfs.search_tokens(type + "::")
        goodmembers = [x for x in members if x[Tokenizer.T_NAME][len(type)+2:].find("::") == -1]
        return goodmembers

    def get_sel_token(self, view):
        selword = view.word(view.sel()[0].end())
        i = selword.begin()
        word = view.substr(selword)
        if i>2 and (view.substr(sublime.Region(i-2, i)) == "->" or view.substr(sublime.Region(i-1, i)) == "." or view.substr(sublime.Region(i-2, i)) == "::"):
            members = self.traverse_members(view, word, i)
            for m in members:
                if m[Tokenizer.T_NAME].endswith("::" + word):
                    return m
            return None

        func =  self.current_function(view)
        if filename in self.cc.functiontokens and func in self.cc.functiontokens[filename]:
            tokens = [x for x in self.cc.functiontokens[filename][func] if x[Tokenizer.T_NAME] == word]
            if len(tokens) > 0:
                return Tokenizer.best_match(tokens)
        return self.tokens(word.lower())
