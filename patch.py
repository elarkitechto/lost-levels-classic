#!/usr/bin/env python3
"""Convert a user-supplied FDS image and apply the final enhancements locally."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import urllib.request
import zlib

ROOT = Path(__file__).resolve().parent
RECIPE = json.loads((ROOT / 'recipe.json').read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def apply_bps(source, patch):
    """BPS1 decoding with source, patch and target checksum validation."""
    require(len(patch) >= 16 and patch[:4] == b'BPS1', 'Invalid BPS patch.')
    src_crc, dst_crc, patch_crc = struct.unpack('<III', patch[-12:])
    require(zlib.crc32(source) == src_crc, 'FDS checksum does not match the official patch.')
    require(zlib.crc32(patch[:-4]) == patch_crc, 'Damaged BPS patch.')
    pos = 4

    def number():
        nonlocal pos
        value, shift = 0, 1
        for _ in range(12):
            require(pos < len(patch) - 12, 'Truncated BPS integer.')
            byte = patch[pos]
            pos += 1
            value += (byte & 127) * shift
            if byte & 128:
                return value
            shift <<= 7
            value += shift
        raise ValueError('BPS integer too large.')

    src_size, dst_size, meta = number(), number(), number()
    require(src_size == len(source) and dst_size <= 2**24, 'Unexpected BPS size.')
    pos += meta
    require(pos <= len(patch) - 12, 'Truncated metadata.')
    output = bytearray()
    src_rel = dst_rel = 0
    while pos < len(patch) - 12:
        action = number()
        size, kind = (action >> 2) + 1, action & 3
        require(len(output) + size <= dst_size, 'BPS output overflow.')
        if kind == 0:
            start = len(output)
            require(start + size <= len(source), 'BPS source overflow.')
            output.extend(source[start:start + size])
        elif kind == 1:
            require(pos + size <= len(patch) - 12, 'Truncated BPS literal.')
            output.extend(patch[pos:pos + size])
            pos += size
        elif kind == 2:
            delta = number()
            src_rel += -(delta >> 1) if delta & 1 else delta >> 1
            require(0 <= src_rel and src_rel + size <= len(source), 'Invalid BPS source offset.')
            output.extend(source[src_rel:src_rel + size])
            src_rel += size
        else:
            delta = number()
            dst_rel += -(delta >> 1) if delta & 1 else delta >> 1
            for _ in range(size):
                require(0 <= dst_rel < len(output), 'Invalid BPS target offset.')
                output.append(output[dst_rel])
                dst_rel += 1
    require(pos == len(patch) - 12 and len(output) == dst_size, 'Incomplete BPS output.')
    require(zlib.crc32(output) == dst_crc, 'Converted ROM checksum mismatch.')
    return bytes(output)


def read_fds(path):
    source = Path(path).read_bytes()
    if source[:4] == b'FDS\x1a':
        require(len(source) == RECIPE['source_size'] + 16, 'Unexpected FDS header or image size.')
        source = source[16:]
    require(len(source) == RECIPE['source_size'], 'Wrong FDS image size.')
    require(hashlib.md5(source).hexdigest() == RECIPE['source_md5'],
            'Unsupported FDS revision. See the required MD5 in README.md. No output was written.')
    return source


def read_patch(path=None):
    if path:
        patch = Path(path).read_bytes()
    else:
        request = urllib.request.Request(RECIPE['patch_url'], headers={'User-Agent': 'NES-Enhancement-Patcher/1.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            patch = response.read(2**20 + 1)
        require(len(patch) <= 2**20, 'Upstream download too large.')
    require(digest(patch) == RECIPE['patch_sha256'], 'Official patch SHA-256 mismatch.')
    return patch


def enhance(base, donor):
    require(digest(base) == RECIPE['base_sha256'], 'Unexpected NES conversion.')
    require(digest(donor) == RECIPE['donor_sha256'], 'Unsupported donor NES revision. See README.md.')
    output = bytearray(base)
    if 'tiles' in RECIPE:
        for dest, src in RECIPE['tiles']:
            tile = donor[32784 + src * 16:32800 + src * 16]
            require(len(tile) == 16, 'Truncated donor tile.')
            offset = RECIPE['chr_offset'] + dest * 16
            output[offset:offset + 16] = tile
        for edit in RECIPE['records']:
            offset = edit['offset']
            before, after = bytes.fromhex(edit['before']), bytes.fromhex(edit['after'])
            require(output[offset:offset + len(before)] == before, 'ROM patch mismatch at offset 0x{:X}.'.format(offset))
            output[offset:offset + len(after)] = after
    else:
        routine = donor[0xdf0:0xdf0 + 37]
        require(digest(routine) == RECIPE['routine_sha256'], 'Donor run routine mismatch.')
        hook = RECIPE['hook_offset']
        routine_at = RECIPE['routine_offset']
        require(output[hook:hook + 20] == bytes.fromhex('a53cd957053003b95705d95a051003b95a05853c'), 'Run hook mismatch.')
        require(output[hook + 20:hook + 22] == b'\x24\xf5', 'Pickup/throw guard mismatch.')
        require(output[routine_at:routine_at + 38] == b'\xff' * 38, 'Run routine space is occupied.')
        output[hook:hook + 20] = b'\x20\x00\xe3' + b'\xea' * 17
        output[routine_at:routine_at + 38] = routine + b'\x60'
    require(digest(output) == RECIPE['output_sha256'], 'Final ROM SHA-256 mismatch.')
    return bytes(output)


def convert(fds, donor, output, upstream_patch=None):
    output = Path(output)
    require(not output.exists(), 'Output already exists. Choose a new filename.')
    source = read_fds(fds)
    donor_data = Path(donor).read_bytes()
    require(digest(donor_data) == RECIPE['donor_sha256'], 'Unsupported donor NES revision. See README.md.')
    result = enhance(apply_bps(source, read_patch(upstream_patch)), donor_data)
    # Exclusive creation also protects against concurrent output creation.
    with output.open('xb') as file:
        file.write(result)
    return output


def gui():
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ImportError as exc:
        raise ValueError('Tkinter is unavailable. Use the command-line example in README.md.') from exc
    app = tk.Tk()
    app.title(RECIPE['title'])
    app.geometry('480x230')
    fds, donor = tk.StringVar(), tk.StringVar()
    tk.Label(app, text=RECIPE['title'], font=('', 16, 'bold')).pack(pady=12)
    def pick(value, title, extension):
        name = filedialog.askopenfilename(title=title, filetypes=[(extension.upper() + ' image', '*.' + extension), ('All files', '*')])
        if name:
            value.set(name)
    tk.Button(app, text='1. Choose original FDS ROM', command=lambda: pick(fds, 'Choose original FDS ROM', 'fds')).pack(pady=4)
    tk.Button(app, text='2. Choose ' + RECIPE['donor_label'], command=lambda: pick(donor, 'Choose donor NES ROM', 'nes')).pack(pady=4)
    def run():
        if not fds.get() or not donor.get():
            messagebox.showerror('Missing ROM', 'Choose both input ROMs first.')
            return
        output = filedialog.asksaveasfilename(title='Save final NES ROM', initialfile=RECIPE['output_name'], defaultextension='.nes')
        if not output:
            return
        try:
            convert(fds.get(), donor.get(), output)
            messagebox.showinfo('Done', 'Final NES ROM created. Your input ROMs were not changed.')
        except Exception as exc:
            messagebox.showerror('Conversion failed', str(exc))
    tk.Button(app, text='3. Create final NES ROM', command=run).pack(pady=12)
    tk.Label(app, text='Only the pinned official conversion patch is downloaded.').pack()
    app.mainloop()


def main():
    parser = argparse.ArgumentParser(description=RECIPE['title'])
    parser.add_argument('fds', nargs='?')
    parser.add_argument('donor', nargs='?')
    parser.add_argument('-o', '--output', default=RECIPE['output_name'])
    parser.add_argument('--upstream-patch', help='Use a locally downloaded official BPS patch (offline mode).')
    args = parser.parse_args()
    try:
        if args.fds is None and args.donor is None:
            gui()
        else:
            require(args.fds and args.donor, 'Provide both the FDS image and donor NES image.')
            convert(args.fds, args.donor, args.output, args.upstream_patch)
            print('Done: final NES ROM created and SHA-256 verified.')
    except Exception as exc:
        print('Error: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
