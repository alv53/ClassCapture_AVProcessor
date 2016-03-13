from distutils.core import setup
from distutils.extension import Extension

import shutil
import os

def wrap_cpp(modname, filenames):
	# wrap C++ vstab code in Python
        setup(name="videostab",
                script_name = 'cpp_py.py',
                script_args = ['build'],
                ext_modules=[
                        Extension(modname, filenames,
                        libraries = ["boost_python", "opencv_core", "opencv_highgui",
"opencv_features2d", "opencv_imgproc", "opencv_video"])
                ])

        # make library file importable in current directory
        shutil.copyfile(os.path.join(os.getcwd(),
'build/lib.linux-x86_64-2.7/videostab.so'), os.path.join(os.getcwd(),
'videostab.so'))

if __name__ == '__main__':
	wrap_cpp("videostab", ["videostab.cpp"])
