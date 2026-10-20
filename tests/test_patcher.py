"""ROM-free validation of the public patcher's format and safety checks."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

spec = importlib.util.spec_from_file_location('patcher', Path(__file__).resolve().parents[1] / 'patch.py')
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)


def number(value):
    out = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        if not value:
            out.append(byte | 128)
            return bytes(out)
        out.append(byte)
        value -= 1


def bps(source, target, actions):
    body = b'BPS1' + number(len(source)) + number(len(target)) + number(0) + actions
    body += struct.pack('<II', zlib.crc32(source), zlib.crc32(target))
    return body + struct.pack('<I', zlib.crc32(body))


class PatcherTests(unittest.TestCase):
    def test_all_bps_actions_and_overlapping_target_copy(self):
        source, target = b'abcd', b'ab!cdcdcd'
        actions = number((2 - 1) * 4)  # SourceRead: ab
        actions += number(1) + b'!'  # TargetRead: !
        actions += number((2 - 1) * 4 + 2) + number(2 * 2)  # SourceCopy: cd
        actions += number((4 - 1) * 4 + 3) + number(3 * 2)  # TargetCopy: cdcd
        self.assertEqual(patcher.apply_bps(source, bps(source, target, actions)), target)

    def test_wrong_source_and_corrupt_patch_are_rejected(self):
        valid = bps(b'abc', b'abc', number(8))
        for source, patch in [(b'xyz', valid), (b'abc', valid[:-1] + bytes([valid[-1] ^ 1]))]:
            with self.assertRaises(ValueError):
                patcher.apply_bps(source, patch)

    def test_invalid_target_copy_and_truncated_data_are_rejected(self):
        bad = bps(b'x', b'y', number(3) + number(0))
        with self.assertRaises(ValueError):
            patcher.apply_bps(b'x', bad)
        for bad in [b'', b'BPS1', b'BPS1' + bytes(20)]:
            with self.assertRaises(ValueError):
                patcher.apply_bps(b'x', bad)

    def test_existing_output_is_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'existing.nes'
            out.write_bytes(b'preserve')
            with self.assertRaises(ValueError):
                patcher.convert('missing.fds', 'missing.nes', out)
            self.assertEqual(out.read_bytes(), b'preserve')

    def test_unknown_game_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            patcher.enhance(b'wrong', b'wrong')
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'unknown.fds'
            source.write_bytes(bytes(patcher.RECIPE['source_size']))
            with self.assertRaises(ValueError):
                patcher.read_fds(source)


if __name__ == '__main__':
    unittest.main()
