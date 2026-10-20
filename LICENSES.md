# Licenses and upstream sources

Reviewed 2026-10-20.

- **New patcher and recipe:** MIT, see LICENSE. The license applies to this project's original work only.
- **Original conversion:** [simplistic6502/smb2j-mmc1](https://github.com/simplistic6502/smb2j-mmc1/tree/2f48615fafbd8a0c395e8aafede6165cbc66ea23), pinned commit `2f48615fafbd8a0c395e8aafede6165cbc66ea23`. No license file or license grant was found in the pinned source tree or README. GitHub's repository API reported `license: null` at review time. Public visibility does not grant a general redistribution or relicensing permission.
- **Distribution boundary:** this repository contains neither the upstream conversion source nor its BPS patch. The patcher retrieves [the author's pinned BPS patch](https://raw.githubusercontent.com/simplistic6502/smb2j-mmc1/2f48615fafbd8a0c395e8aafede6165cbc66ea23/smb2j-mmc1.bps) directly and validates SHA-256 `ad8208b41553c82373abfce41f7bd704c09b71df0d83faa6ae5de07d40834a79`. Users can supply that same patch offline. This project does not claim the authors granted a license to their conversion.
- **Game data:** supplied by the user. No ROM, BIOS, extracted graphics or commercial game routine is shipped. The graphics come from the required donor ROM during local patching.
- **Forks:** this repository is an independent companion tool, not a relicensed fork of the unlicensed conversion. Bundling the original conversion or its patch would require resolving the applicable rights separately.

GitHub explains the distinction between public visibility, forking on GitHub and an open-source license in [Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).
