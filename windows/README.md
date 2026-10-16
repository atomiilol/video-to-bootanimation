# Windows video / bootanimation converter

Requires Windows 10/11, Python 3.9+ from https://www.python.org/downloads/windows/
and a Windows FFmpeg build containing ffmpeg.exe and ffprobe.exe (see
https://ffmpeg.org/download.html). Enable Python on PATH. Place both FFmpeg
executables beside the batch files, or add their directory to PATH.
No Android device, root, or Android binaries are required for conversion.

Extract the entire release ZIP before running. Drag a video onto
`video-to-boot.bat`, or a bootanimation ZIP onto `boot-to-video.bat`.
Output is saved beside the input, with `-bootanimation.zip` or `-video.mp4`
appended to its stem. Existing outputs are never overwritten.

From Command Prompt:

```bat
video-to-boot.bat "C:\Videos\my video.mp4" "C:\Videos\bootanimation.zip" --fps 30 --width 1080 --height 1920
boot-to-video.bat "C:\Videos\bootanimation.zip" "C:\Videos\preview.mp4"
```

Video-to-boot defaults to 30 FPS and the input dimensions. It writes uncompressed
PNG entries and an Android desc.txt with one infinitely looping part.
Boot-to-video supports standard p/c parts, finite repetitions, and frame pauses.
Infinite parts play once so the MP4 can finish. Images are sorted by filename.
Audio, dynamic colors, trim metadata, and Android boot-completion behavior are
not reproduced; unsupported descriptor directives fail with an error.
Use modest dimensions and FPS first: decoded frames can require substantial
temporary disk space. Only convert trusted animation archives.

This creates a bootanimation ZIP, not a flashable Magisk module. Installing an
animation on a device is a separate step. Samsung QMG animations are unsupported.

The engine is tested on Linux with FFmpeg; batch launchers still need a Windows
runtime check. The release does not bundle Python or FFmpeg.
