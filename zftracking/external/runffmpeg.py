"""executes external program: ffmpeg"""

import subprocess
import os


class Ffmpeg:
    """class for ffmpeg execution"""
    def __init__(self, infile, outfile):
        self.ffmpeg_location = "ffmpeg"
        script_dir = os.path.dirname(__file__)
        rel_path = "data/ffmpeg_location.txt"
        abs_file_path = os.path.join(script_dir, rel_path)
        with open(abs_file_path) as dat:
            for line in dat:
                if line != '':
                    self.ffmpeg_location = line.rstrip('\n')
        self.infile = '"' + infile + '"'
        self.outfile = '"' + outfile + '"'
        self.filter = False
        self.pix_fmt = False
        self.vcodec = False
        self.f = False
        self.ss = False
        self.vframes = False
        self.width = False

    def run(self):
        """prepares arguments and executes ffmpeg as a subprocess"""
        args = self.ffmpeg_location + " -hide_banner -loglevel panic "
        if self.ss:
            args += '-ss ' + self.ss + " "
        args += "-i " + self.infile + " "
        if self.filter:
            args += '-filter:v "' + self.filter + '" '
        if self.pix_fmt:
            args += '-pix_fmt ' + self.pix_fmt + " "
        if self.vcodec:
            args += '-vcodec ' + self.vcodec + " "
        if self.width:
            args += '-vf scale=' + str(self.width) + ':-1 '
        if self.f:
            args += '-f ' + self.f + " "
        if self.vframes:
            args += '-vframes ' + self.vframes + " "
        args += self.outfile
        print("running ffmpeg with:")
        print(args)
        d = subprocess.run(args, shell=True)
        return d
