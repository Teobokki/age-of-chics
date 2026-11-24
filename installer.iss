#define MyVer "2.5.1"
#define MyApp "AGE OF CHICS™ BY HYPERION"
#define MyExe "AGE OF CHICS"
[Setup]
AppId={{91B2B294-5897-4C19-BCAB-2DE8943F2CB8}
AppName={#MyApp}
AppVersion={#MyVer}
AppVerName={#MyApp} {#MyVer}
AppPublisher=EX Inc./HYPERION DIGITAL
AppPublisherURL=https://github.com/Teobokki/age-of-chics
AppCopyright=©2026 EX Inc./HYPERION DIGITAL ©2026
VersionInfoVersion={#MyVer}.0
VersionInfoCompany=EX Inc.
VersionInfoCopyright=©2026 EX Inc./HYPERION DIGITAL ©2026
VersionInfoProductName={#MyApp}
VersionInfoDescription={#MyApp} Setup
DefaultDirName={localappdata}\Programs\{#MyExe}
DefaultGroupName={#MyApp}
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
UsePreviousPrivileges=no
UsePreviousAppDir=yes
OutputDir=dist
OutputBaseFilename=AGE-OF-CHICS-Setup-{#MyVer}
SetupIconFile=assets\logo.ico
WizardImageFile=assets\wizard_large.bmp,assets\wizard_large2x.bmp
WizardSmallImageFile=assets\wizard_small.bmp,assets\wizard_small2x.bmp
UninstallDisplayIcon={app}\{#MyExe}.exe
UninstallDisplayName={#MyApp}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
RestartApplications=no
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#MyExe}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs uninsrestartdelete

[Icons]
Name: "{group}\{#MyApp}"; Filename: "{app}\{#MyExe}.exe"; IconFilename: "{app}\{#MyExe}.exe"
Name: "{group}\Uninstall {#MyApp}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyApp}"; Filename: "{app}\{#MyExe}.exe"; IconFilename: "{app}\{#MyExe}.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyExe}.exe"; Description: "Launch {#MyApp}"; Flags: nowait postinstall skipifsilent
