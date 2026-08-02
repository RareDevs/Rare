#define AppName "Rare"
#define AppExeName "Rare.exe"
; Defines expected to be passed via arguments to iscc:
; - AppVersion: The application version (no format requirements)
; - NumericVersion: Application version in the format of VersionInfoVersion (https://jrsoftware.org/ishelp/topic_setup_versioninfoversion.htm)
; - SourceDir: Path to the repository root. Used to pull assets like the logo
; - FilesDir: Path to a directory containing the actual executable files that should be installed. This should have a
;             "Rare.exe" in its top level

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
ArchitecturesAllowed={#AppArchitecture}
ArchitecturesInstallIn64BitMode={#AppArchitecture}
DefaultDirName={autopf}\Rare
DisableProgramGroupPage=yes
DisableWelcomePage=no
LicenseFile=LICENSE
MinVersion=10.0
OutputDir=build
OutputBaseFilename=Rare-{#AppVersion}-{#AppPlatform}-setup
PrivilegesRequiredOverridesAllowed=dialog
SetupArchitecture=x64
SetupIconFile=rare\resources\images\Rare.ico
ShowLanguageDialog=auto
SolidCompression=yes
SourceDir={#SourceDir}
UninstallDisplayIcon={app}\{#AppExeName}
VersionInfoVersion={#NumericVersion}
WizardImageFile=packaging\innosetup\image.png
WizardImageFileDynamicDark=packaging\innosetup\image.png
WizardSmallImageFile=rare\resources\images\Rare.png
WizardSmallImageFileDynamicDark=rare\resources\images\Rare.png
WizardStyle=modern dynamic

#call EmitLanguagesSection

[Files]
Source: "{#FilesDir}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall
