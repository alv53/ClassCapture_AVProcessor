from distutils.core import setup
from distutils.extension import Extension

setup(name="PackageName",
    ext_modules=[
        Extension("vs", ["vs.cpp"],
        libraries = ["boost_python", "opencv_core", "opencv_highgui", "opencv_features2d", "opencv_imgproc", "opencv_video"])
    ])
