import sublime
import sublime_plugin
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import _thread
import threading
import platform
import os

def MakeHandlerClassFromFilename(file_full_path, tests_relative_dir, tests_file_suffix):
    if not tests_file_suffix: tests_file_suffix = "__tests"

    class HandleRequests(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                tests = json.loads(body.decode('utf8'))
                tests = tests["tests"]
                ntests = []
                for test in tests:
                    ntest = {
                        "test": test["input"],
                        "correct_answers": [test["output"].strip()]
                    }
                    ntests.append(ntest)
                dir_path = os.path.join(os.path.dirname(file_full_path), tests_relative_dir) \
                    if tests_relative_dir else os.path.dirname(file_full_path)
                file_name = os.path.basename(file_full_path) + tests_file_suffix
                tests_file_path = os.path.join(dir_path, file_name)
                print("[FastOlympicCodingHook] New test cases: \"%s\"" % tests_file_path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                with open(tests_file_path, "w") as f:
                    f.write(json.dumps(ntests))
            except Exception as e:
                print("[FastOlympicCodingHook] Error handling POST - " + str(e))
            threading.Thread(target=self.server.shutdown, daemon=True).start()
    return HandleRequests


class CompetitiveCompanionServer:
    def startServer(view):
        host = 'localhost'
        port = 12345
        foc_settings = sublime.load_settings("FastOlympicCoding.sublime-settings")
        tests_relative_dir = foc_settings.get("tests_relative_dir")
        tests_file_suffix = foc_settings.get("tests_file_suffix")
        print("[FastOlympicCodingHook] Server has been started.")
        view.set_status("foc_hook", "Listening...")
        HandlerClass = MakeHandlerClassFromFilename(view.file_name(), tests_relative_dir, tests_file_suffix)
        httpd = HTTPServer((host, port), HandlerClass)
        httpd.serve_forever()
        print("[FastOlympicCodingHook] Server has been shutdown.")
        view.erase_status("foc_hook")


class FastOlympicCodingHookCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            _thread.start_new_thread(CompetitiveCompanionServer.startServer,
                                     (self.view,))
        except Exception as e:
            print("Error: unable to start thread - " + str(e))
