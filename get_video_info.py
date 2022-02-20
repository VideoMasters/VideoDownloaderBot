""" Get video attributes and thumbnail """

import tempfile
from subprocess import getstatusoutput


def get_video_attributes(file: str):
    """Returns video duration, width, height"""

    class FFprobeAttributesError(Exception):
        """Exception if ffmpeg fails to generate attributes"""

    cmd = (
        "ffprobe -v error -show_entries format=duration "
        + "-of default=noprint_wrappers=1:nokey=1 "
        + "-select_streams v:0 -show_entries stream=width,height "
        + f" -of default=nw=1:nk=1 '{file}'"
    )
    res, out = getstatusoutput(cmd)
    if res != 0:
        raise FFprobeAttributesError(out)
    width, height, dur = out.split("\n")
    return (int(float(dur)), int(width), int(height))


def get_video_thumb(file: str):
    """Returns path to video thumbnail"""

    class FFprobeThumbnailError(Exception):
        """Exception if ffmpeg fails to generate thumbnail"""

    thumb_file = tempfile.NamedTemporaryFile(suffix=".jpg").name
    duration, width, height = get_video_attributes(file)
    dur = str(int(duration / 2))
    size = f"{width}x{height}"
    cmd = (
        f"ffmpeg -v error -ss {dur} -i '{file}'  -vframes 1 "
        + f"-s {size} {thumb_file}"
    )
    res, out = getstatusoutput(cmd)
    if res != 0:
        raise FFprobeThumbnailError(out)
    return thumb_file
