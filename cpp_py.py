from distutils.core import setup
from distutils.extension import Extension

import shutil
import os

def wrap_cpp(modname, filenames):
        """Make C++ files importable in the current directory as one Python
module.
       
        Args:
                modname: str, desired name for the resulting Python module.
                filenames: list of str, names of the C++ files that will comprise
the module.
         """
	# wrap C++ vstab code in Python
        setup(name=modname,
                script_name = 'cpp_py.py',
                script_args = ['build'],
                ext_modules=[
                        Extension(modname, filenames,
                        libraries = ["boost_python", "opencv_core", "opencv_highgui",
"opencv_features2d", "opencv_imgproc", "opencv_video"])
                ])

        # make module importable in current directory
        shutil.copyfile(os.path.join(os.getcwd(),
'build/lib.linux-x86_64-2.7', modname + '.so'), os.path.join(os.getcwd(),
'videostab.so'))

if __name__ == '__main__':
	wrap_cpp("videostab", ["videostab.cpp"])
