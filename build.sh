#!/bin/sh
# ONE Windows build: PyInstaller onedir -> Inno Setup installer, plus a standalone one-file portable .exe (no zip)
set -e
export PATH=/workspace/wine-portable/current/bin:$PATH WINEPREFIX=/workspace/exwifi/.wine WINEDEBUG=-all
cd /workspace/age-of-chics
V=1.0.1
rm -rf build dist build1f
wine 'C:\Python311\python.exe' -m PyInstaller --noconfirm "AGE OF CHICS.spec" > pyi.log 2>&1; echo PYI_DONE
wine 'C:\InnoSetup\ISCC.exe' installer.iss > iss.log 2>&1; echo ISS_DONE
AOC_ONEFILE=1 wine 'C:\Python311\python.exe' -m PyInstaller --noconfirm --workpath build1f "AGE OF CHICS.spec" > pyi1f.log 2>&1; echo PYI1F_DONE
cd dist && mv -f "AGE OF CHICS Portable.exe" "AGE-OF-CHICS-Portable-$V.exe"
ls -la "AGE-OF-CHICS-Setup-$V.exe" "AGE-OF-CHICS-Portable-$V.exe"
sha256sum "AGE-OF-CHICS-Setup-$V.exe" "AGE-OF-CHICS-Portable-$V.exe"
