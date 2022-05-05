import sys
from os.path import join, dirname, realpath

def resource_path(*args):
    fpath = "resources"
    if len(args):
        fpath = join(fpath, *args)
    if hasattr(sys, '_MEIPASS'):
        return join(sys._MEIPASS, fpath)
    return join(dirname(realpath(__file__)), '..', '..', fpath)
