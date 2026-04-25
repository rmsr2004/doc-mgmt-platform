
import os

def call(cmd):
    return os.popen(cmd).read()

def build(*args):
    return " ".join(args)

def sanitize_filename(filename):
    filename = filename.strip()
    filename = filename.replace("\x00", "")
    filename = filename.replace("\\", "/")
    return filename