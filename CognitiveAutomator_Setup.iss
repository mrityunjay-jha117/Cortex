; CognitiveAutomator_Setup.iss
; Inno Setup 6.x script — produces a signed Windows installer
;
; Build with:
;   iscc CognitiveAutomator_Setup.iss
;
; Output: Output\CognitiveAutomator-Setup-1.0.0.exe

#define AppName      "Cognitive Automator"
#define AppVersion   "1.0.0"
#define AppPublisher "Cognitive Automator"
#define AppURL       "https://github.com/your-org/cognitive-automator"
#define AppExeName   "CognitiveAutomator.exe"
#define AppDescription "LLM-Powered Windows Automation Framework"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
OutputDir=Output
OutputBaseFilename=CognitiveAutomator-Setup-{#AppVersion}
; Code signing — replace with your cert path:
; SignTool=signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f "cert.pfx" /p "$PASSWORD" $f
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0
WizardStyle=modern
WizardSmallImageFile=cognitive_automator\assets\installer_banner_small.bmp
; WizardImageFile=cognitive_automator\assets\installer_banner.bmp
SetupIconFile=cognitive_automator\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppDescription}
VersionInfoCompany={#AppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenuicon";   Description: "Create Start Menu shortcut";   GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "fileassociation"; Description: "Associate .cogauto files with {#AppName}"; GroupDescription: "File Associations"; Flags: checkedonce

[Files]
; Main executable (built by PyInstaller)
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Sample automations
Source: "examples\*.cogauto"; DestDir: "{app}\examples"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; Documentation
Source: "README.md";    DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LICENSE.txt";  DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Desktop (optional)
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; .cogauto file association
Root: HKCU; Subkey: "Software\Classes\.cogauto"; ValueType: string; ValueName: ""; ValueData: "CognitiveAutomator.Automation"; Flags: uninsdeletekey; Tasks: fileassociation
Root: HKCU; Subkey: "Software\Classes\CognitiveAutomator.Automation"; ValueType: string; ValueName: ""; ValueData: "Cognitive Automator Workflow"; Flags: uninsdeletekey; Tasks: fileassociation
Root: HKCU; Subkey: "Software\Classes\CognitiveAutomator.Automation\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Flags: uninsdeletekey; Tasks: fileassociation
Root: HKCU; Subkey: "Software\Classes\CognitiveAutomator.Automation\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: fileassociation

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName,'&','&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data on uninstall (optional — comment out to preserve user automations)
; Type: filesandordirs; Name: "{userappdata}\CognitiveAutomator"

[Code]
// Optional: check for Windows 10+ before installing
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  if Version.Major < 10 then begin
    MsgBox('Cognitive Automator requires Windows 10 or later.', mbError, MB_OK);
    Result := False;
  end else
    Result := True;
end;
