# Final build verification

The enhancement stage reproduces the released final ROM SHA-256 below. The patcher verifies the official BPS checksum, its pinned SHA-256, both ROM revisions and the final output hash. It refuses unknown inputs and existing output files.

The complete FDS-to-final conversion was verified using the required FDS and donor NES inputs, including an offline run with the pinned official patch.

Final ROM SHA-256: `758880642391ba7f52a4d4c2c68082e3927f9a896705b37e78a4b9f17d4dc448`

Automated ROM-free checks: `python3 -m unittest discover -s tests -v`. Tests cover all four BPS actions, overlapping copies, invalid checksums and offsets, unsupported ROMs, and preserving an existing output file.

Maze feedback was tested by executing the original and modified checkpoint routine in a 6502 emulator across 896 cases. Both versions matched in registers and game RAM except for the expected sound queue writes. One- and two-checkpoint passes, loopbacks, airborne checks and occupied sound queues were covered.

The castle firebar pivot hook was exercised in 11,520 emulated CPU cases covering geometry, character size, crouching, velocity, game mode, and collision guards. A direct firebar hit outside the pivot-bump frame still takes the original injury path. These are targeted CPU tests. The revised build was also approved after a console playtest.
