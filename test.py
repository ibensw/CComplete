import sublime, sublime_plugin
import os, sys
import time

class CCompleteTest(sublime_plugin.ApplicationCommand):
    testview = None;
    plugin = sys.modules["CComplete.ccomplete_plugin"].CCompletePlugin()

    def setup(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.testview = sublime.active_window().open_file(dir_path+"/test/test.c")
        self.plugin.on_activated_async(self.testview)
        if not self.plugin.ready:
            time.sleep(1)
        return self.plugin.ready

    def get_completions_for_test(self, testname):
        self.setup()
        testline = self.testview.find("/* TEST_%s */" % testname, 0, sublime.LITERAL)
        testline = self.testview.line(testline)
        self.testview.sel().clear()
        self.testview.sel().add(sublime.Region(testline.b, testline.b))
        output=self.plugin.on_query_completions(self.testview, "", [testline.b])
        return output[0]

    def perform_single_test(self, testname, expected):
        out = self.get_completions_for_test(testname)
        if (out == expected):
            print("Test %s passed" % testname)
            return True
        print("Test %s FAILURE" % testname)
        print("Output:   %s" % out)
        print("Expected: %s" % expected)
        return False

    def run(self):
        print("Running automated tests...")
        self.perform_single_test("name1", [['fgh1\tint', 'fgh1'], ['abc1\tint', 'abc1'], ['def1\tint', 'def1']])
        self.perform_single_test("name2", [['fgh2\tint', 'fgh2'], ['abc2\tint', 'abc2'], ['def2\tint', 'def2']])
        self.perform_single_test("root_struct_a", [['a1\tint', 'a1'], ['a2\tint', 'a2']])
        self.perform_single_test("root_struct_b", [['b1\tint', 'b1'], ['b2\tint', 'b2']])
        self.perform_single_test("root_struct_c", [['c1\tint', 'c1'], ['c2\tint', 'c2']])
        self.perform_single_test("root_struct_d", [['d1\tint', 'd1'], ['d2\tint', 'd2']])
        self.perform_single_test("root_union_a", [['a1\tint', 'a1'], ['a2\tint', 'a2']])
        self.perform_single_test("root_union_b", [['b1\tint', 'b1'], ['b2\tint', 'b2']])
        self.perform_single_test("root_union_c", [['c1\tint', 'c1'], ['c2\tint', 'c2']])
        self.perform_single_test("root_union_d", [['d1\tint', 'd1'], ['d2\tint', 'd2']])
        self.perform_single_test("mystruct", [['mem37\tint', 'mem37'], ['internA\t(Anonymous)', 'internA'], ['internB\ti17', 'internB'], ['mem36\tint', 'mem36'], ['mem40\ti16', 'mem40'], ['mem2\tint', 'mem2'], ['internA\t(Anonymous)', 'internA'], ['internB\ti2', 'internB'], ['mem1\tint', 'mem1'], ['mem5\ti1', 'mem5'], ['a1\ttA', 'a1'], ['a2\tuA', 'a2'], ['b1\ttB', 'b1'], ['b2\tuB', 'b2'], ['c1\trootStructC', 'c1'], ['c2\trootUnionC', 'c2'], ['member\tint', 'member'], ['member1\t(Anonymous)', 'member1'], ['member2\tisa', 'member2'], ['member3\tisb', 'member3'], ['member4\t(Anonymous)', 'member4'], ['member5\tiua', 'member5'], ['member6\tiub', 'member6']])
