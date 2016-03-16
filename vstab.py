import cpp_py
import os
import subprocess


def stab(inname, outname):
    """Stabilize a video file.

    Args:
	inname: str, filename of the input video.
	outname: str, filename of the resulting stabilized video.

    Returns:
	None
	Stabilized video will be saved in the current directory.
	"""
    # make the C++ vstab code usable in Python
    cpp_py.wrap_cpp("videostab", ["videostab.cpp"])
    import videostab

    frames_dir = os.path.join(os.getcwd(), 'images')
    if not os.path.exists(frames_dir):
    	os.makedirs(frames_dir)
    else:
        for f in os.listdir('images'):
            os.remove(os.path.join('images', f))

    vid_metadata = subprocess.check_output(['ffprobe', inname],
            stderr=subprocess.STDOUT)
    if vid_metadata.find('rotate') == -1:
        rotation = 0
    else:
        vid_metadata =  vid_metadata[vid_metadata.find('rotate'):]
        rotation = int(vid_metadata[vid_metadata.find(': ')+2:
            vid_metadata.find('\n')])

    # generate stabilized frames
    fps = videostab.stabilize(inname, rotation)

    #  create video from frames
    outname_split = outname.rsplit('.')
    if len(outname_split) > 1 and outname_split[-1] in ['mp4', 'avi', 'mov']:
        outname_muted = ''.join(outname_split[:-1]) + '_muted' + '.mp4'
    else:
        outname_muted = outname + '.mp4'
    subprocess.call(['ffmpeg', '-f', 'image2', '-r', str(fps), '-i', 'images/%08d.jpg',
       '-vcodec', 'mpeg4', '-y', outname_muted])

    # copy original audio to the stabilized video
    subprocess.call(['ffmpeg', '-i', outname_muted, '-i', inname,
        '-c', 'copy', '-map', '0:0', '-map', '1:1?', '-shortest', '-y', outname])


import sys

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: ' + '$ python vstab.py in.mp4 out.mp4')
    else:
        stab(sys.argv[1], sys.argv[2])
