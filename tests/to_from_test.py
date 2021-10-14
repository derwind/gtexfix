import sys, os
import shutil
import hashlib
import unittest

file_dir = os.path.abspath(os.path.dirname(__file__))
temp_files = list(map(lambda v: os.path.join(file_dir, v), [
    "example.tex",
    "example_0.txt",
    "example_0.tex",
    "gtexfix_commands",
    "gtexfix_comments",
    "gtexfix_latex",
]))

def md5sum(file):
    with open(file, "rb") as fin:
        data = fin.read()
    return hashlib.md5(data).hexdigest()

class ToFromTest(unittest.TestCase):
    def setUp(self):
        shutil.copy2(os.path.join(file_dir, "..", "to.py"), os.path.join(file_dir, "to2.py"))
        shutil.copy2(os.path.join(file_dir, "..", "from.py"), os.path.join(file_dir, "from2.py"))

    def tearDown(self):
        for file in temp_files + [os.path.join(file_dir, "to2.py"), os.path.join(file_dir, "from2.py")]:
            if not os.path.exists(file):
                continue
            os.remove(file)

    def test_to_from(self):
        from to2 import convert_to
        from from2 import convert_from

        os.chdir(file_dir)

        target_tex_file = os.path.join(file_dir, "example.tex")
        converted_text_file = os.path.join(file_dir, "example_0.txt")
        converted_tex_file = os.path.join(file_dir, "example_0.tex")
        shutil.copy2(os.path.join(file_dir, "..", "examples", "example.tex"), target_tex_file)
        convert_to(target_tex_file)
        convert_from(converted_text_file)

        self.assertEqual(md5sum(target_tex_file), md5sum(converted_tex_file))

if __name__ == '__main__':
    sys.exit(unittest.main())
