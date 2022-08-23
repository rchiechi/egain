import os
from datetime import datetime
from types import SimpleNamespace

def createOptions():
    opts = SimpleNamespace()
    save_path = ''
    try:
        save_path = os.getcwd()
    except KeyError:
        save_path = os.path.expanduser('~')
    opts.save_path = save_path
    dt = datetime.now()
    opts.output_file_name = dt.strftime('%Y%m%d_%H%M_')
    return opts

# class Options(SimpleNamespace):
#
#     def __init__(self):
#         super().__init__()
#         self.__setSavepath()
#         self.__setOutputfilename()
#
#     def __setSavepath(self):
#         save_path = ''
#         try:
#             save_path = os.getcwd()
#         except KeyError:
#             save_path = os.path.expanduser('~')
#         self.__dict__.__setattr___('save_path', save_path)
#
#     def __setOutputfilename(self):
#         dt = datetime.now()
#         self.__dict__.__setattr__('output_file_name',
#                      dt.strftime('%Y%m%d_%H%M_data.txt'))