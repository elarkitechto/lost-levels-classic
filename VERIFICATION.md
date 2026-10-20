# Final build verification

The enhancement stage reproduces the released final ROM SHA-256 below. The patcher verifies the official BPS checksum, its pinned SHA-256, both ROM revisions and the final output hash. It refuses unknown inputs and existing output files.

The complete FDS-to-final conversion was verified using the required FDS and donor NES inputs, including an offline run with the pinned official patch.

Final ROM SHA-256: `6df9af8cd888a6354c2ec39cceae9cfc0c5b5c653b8dc7cb5bc04d3ace612fae`

Automated ROM-free checks: `python3 -m unittest discover -s tests -v`. Tests cover all four BPS actions, overlapping copies, invalid checksums and offsets, unsupported ROMs, and preserving an existing output file.
