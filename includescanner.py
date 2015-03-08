import os.path, re

class IncludeScanner:
    baseregex = re.compile('^#include\s+"(.*)"')
    sysregex = re.compile('^#include\s+<(.*)>')

    @staticmethod
    def find_file(basepaths, filename):
        if os.path.isabs(filename):
            return filename
        for path in basepaths:
            filepath = os.path.join(path, filename)
            if os.path.isfile(filepath):
                return filepath
        return None

    @staticmethod
    def scan_file(filename, basepaths = [], syspaths = []):
        if filename and os.path.isfile(filename):
            findsys = len(syspaths) > 0

            basepaths.insert(0, os.path.dirname(filename))
            includes = set([])
            if not os.path.isfile(filename):
                return includes

            with open(filename, 'r') as fp:
                for line in fp:
                    line = line.lstrip();
                    if line.startswith("#include"):
                        baseinc = IncludeScanner.baseregex.search(line)
                        if baseinc:
                            fullpath = IncludeScanner.find_file(basepaths, baseinc.group(1))
                            if fullpath:
                                includes.add(fullpath)
                        elif findsys:
                            sysinc = IncludeScanner.sysregex.search(line)
                            if sysinc:
                                fullpath = IncludeScanner.find_file(syspaths, sysinc.group(1))
                                if fullpath:
                                    includes.add(fullpath)
            return includes
        else:
            return set([])

    @staticmethod
    def scan_recursive(filename, basepaths = [], syspaths = []):
        todo=[filename]
        done=[]

        while len(todo) > 0:
            progress = todo.pop(0)
            done.append(progress)
            includes = IncludeScanner.scan_file(progress, basepaths, syspaths)
            for i in includes:
                if i not in todo and i not in done:
                    todo.append(i)
        return done
