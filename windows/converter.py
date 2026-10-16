"""Windows batch converter engine. Requires Python 3.9+ and FFmpeg."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def tool(name):
    local = Path(__file__).resolve().parent / (name + '.exe')
    result = str(local) if local.is_file() else shutil.which(name)
    if not result:
        raise ValueError(f'{name} missing: place {name}.exe beside the batch files or add it to PATH')
    return result


def run(args):
    subprocess.run(args, check=True)


def video_to_boot(source, target, args, work):
    info = json.loads(subprocess.check_output([
        tool('ffprobe'), '-v', 'error', '-select_streams', 'v:0',
        '-show_streams', '-of', 'json', str(source)]))['streams'][0]
    width, height = args.width or info['width'], args.height or info['height']
    frames = work / 'part0'
    frames.mkdir()
    run([tool('ffmpeg'), '-nostdin', '-v', 'error', '-i', str(source),
         '-vf', f'fps={args.fps},scale={width}:{height}',
         str(frames / '%06d.png')])
    images = sorted(frames.glob('*.png'))
    if not images:
        raise ValueError('Video produced no frames')
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('desc.txt', f'{width} {height} {args.fps}\np 0 0 part0\n')
        for image in images:
            archive.write(image, 'part0/' + image.name)


def boot_to_video(source, target, args, work):
    sequence = work / 'frames'
    sequence.mkdir()
    count = 0
    with zipfile.ZipFile(source) as archive:
        lines = [line.strip() for line in archive.read('desc.txt').decode('utf-8-sig').splitlines()
                 if line.strip() and not line.lstrip().startswith('#')]
        width, height, fps = map(int, lines[0].split()[:3])
        if min(width, height, fps) <= 0:
            raise ValueError('Invalid bootanimation dimensions or FPS')
        for line in lines[1:]:
            fields = line.split()
            if fields[0] not in ('p', 'c') or len(fields) < 4:
                raise ValueError('Unsupported descriptor directive: ' + line)
            repeats, pause = map(int, fields[1:3])
            if repeats < 0 or pause < 0:
                raise ValueError('Negative loop count or pause')
            part = fields[3].rstrip('/') + '/'
            names = sorted(n for n in archive.namelist()
                           if n.startswith(part) and '/' not in n[len(part):]
                           and Path(n).suffix.lower() in ('.png', '.jpg', '.jpeg'))
            if not names:
                raise ValueError('No frames in ' + part)
            # Infinite Android loops become one pass in a finite MP4.
            for _ in range(max(1, repeats)):
                for name in names:
                    destination = sequence / f'{count:08d}.png'
                    with archive.open(name) as src, destination.open('wb') as dst:
                        shutil.copyfileobj(src, dst)
                    count += 1
                for _ in range(pause):
                    shutil.copyfile(sequence / f'{count - 1:08d}.png', sequence / f'{count:08d}.png')
                    count += 1
    if not count:
        raise ValueError('No animation frames found')
    run([tool('ffmpeg'), '-nostdin', '-v', 'error', '-framerate', str(fps),
         '-i', str(sequence / '%08d.png'), '-vf',
         f'scale={width}:{height},pad=ceil(iw/2)*2:ceil(ih/2)*2',
         '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['video-to-boot', 'boot-to-video'])
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path, nargs='?')
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--width', type=int)
    parser.add_argument('--height', type=int)
    args = parser.parse_args()
    try:
        source = args.input.resolve(strict=True)
        target = (args.output or source.with_name(
            source.stem + ('-bootanimation.zip' if args.mode == 'video-to-boot' else '-video.mp4'))).resolve()
        if target.exists():
            raise ValueError('Output already exists; choose a new filename: ' + str(target))
        if any(n is not None and n <= 0 for n in [args.fps, args.width, args.height]):
            raise ValueError('FPS, width, and height must be positive')
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            result = work / ('result.zip' if args.mode == 'video-to-boot' else 'result.mp4')
            operation = video_to_boot if args.mode == 'video-to-boot' else boot_to_video
            operation(source, result, args, work)
            # Exclusive creation preserves existing files even if another process creates one.
            with result.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
        print('Created:', target)
        return 0
    except (OSError, ValueError, KeyError, IndexError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print('Conversion failed:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
