#!/usr/bin/env python3
"""Package reviewed tracked files without Git data or workstation metadata."""
import argparse
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(filter(None, files)):
            info = zipfile.ZipInfo(ROOT.name + '/' + name, (2026, 10, 20, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (ROOT / name).read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    subprocess.run(['python3', str(ROOT / 'tools/sanitize-release.py'), str(args.output)], check=True)


if __name__ == '__main__':
    main()
