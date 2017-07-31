"""executes external program: fiji"""

import subprocess
import os


class ImageJMacro:
    """class for ImageJ macro execution"""
    def __init__(self, macro):
        self.macro = macro
        self.fiji_location = "/home/nils/Fiji.app/ImageJ-linux64"
        script_dir = os.path.dirname(__file__)
        rel_path = "data/fiji_location.txt"
        abs_file_path = os.path.join(script_dir, rel_path)
        with open(abs_file_path) as dat:
            for line in dat:
                if line != '':
                    self.fiji_location = line.rstrip('\n')

    def run(self, arguments):
        """prepares all arguments and executes the macro as a subprocess"""
        args = self.fiji_location + " --headless -macro "
        args += self.macro + " '"
        for arg in arguments:
            args += arg + "#"
        args += "'"
        print("running ImageJ with:")
        print(args)
        d = subprocess.run(args, shell=True)
        return d
