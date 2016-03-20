import shutil

# "Stupid" algorithm that does nothing.
def createCopy(inname, outname):
	shutil.copyfile(inname, outname)
