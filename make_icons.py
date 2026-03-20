#!/usr/bin/env python3
"""Generate PWA icons — run once, then commit the output PNG files."""
import struct, zlib, math, os

def _encode_png(size, pixels_rgb):
    rows = []
    for y in range(size):
        row = b'\x00' + bytes(c for px in pixels_rgb[y * size:(y + 1) * size] for c in px)
        rows.append(row)
    compressed = zlib.compress(b''.join(rows), 9)

    def chunk(tag, data):
        body = tag + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)

    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    idat = chunk(b'IDAT', compressed)
    iend = chunk(b'IEND', b'')
    return b'\x89PNG\r\n\x1a\n' + ihdr + idat + iend


def make_icon(size):
    BG        = (22, 22, 40)    # dark navy
    BALL_W    = (238, 238, 238) # ball white
    BALL_B    = (38, 38, 50)    # ball black patches
    BORDER    = (38, 38, 50)

    cx = cy = (size - 1) / 2.0
    ball_r  = size * 0.40
    inner_r = ball_r - max(2, size * 0.025)

    # Six patch centres around a central one (classic football look)
    pr = ball_r * 0.40   # distance of outer patches from centre
    patch_r = ball_r * 0.21  # radius of each patch
    patches = [(0.0, 0.0)] + [
        (pr * math.sin(math.radians(a)), -pr * math.cos(math.radians(a)))
        for a in range(0, 360, 60)
    ]

    pixels = []
    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > ball_r:
                pixels.append(BG)
            elif d > inner_r:
                pixels.append(BORDER)
            elif any(math.hypot(dx - px, dy - py) < patch_r for px, py in patches):
                pixels.append(BALL_B)
            else:
                pixels.append(BALL_W)

    return _encode_png(size, pixels)


os.makedirs('static/icons', exist_ok=True)
for sz in (180, 192, 512):
    data = make_icon(sz)
    path = f'static/icons/icon-{sz}.png'
    with open(path, 'wb') as f:
        f.write(data)
    print(f'  Created {path}  ({len(data):,} bytes)')
print('Done.')
