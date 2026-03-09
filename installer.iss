[Setup]
AppId={{E4B2A1C0-7D3F-4A8E-B5C6-9F1D2E3A4B5C}
AppName=Yorick Build Advisor
AppVersion=1.0.0
AppPublisher=Yorick Build Advisor
AppPublisherURL=https://github.com/yorick-build-advisor
DefaultDirName={localappdata}\YorickBuildAdvisor
DefaultGroupName=Yorick Build Advisor
UninstallDisplayIcon={app}\YorickBuildAdvisor.exe
OutputDir=installer_output
OutputBaseFilename=YorickBuildAdvisor_Setup
SetupIconFile=static\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "taskbarpin"; Description: "Pin to Taskbar"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\YorickBuildAdvisor.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Yorick Build Advisor"; Filename: "{app}\YorickBuildAdvisor.exe"; AppUserModelID: "Yorick.BuildAdvisor.1.0"
Name: "{group}\Uninstall Yorick Build Advisor"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Yorick Build Advisor"; Filename: "{app}\YorickBuildAdvisor.exe"; Tasks: desktopicon; AppUserModelID: "Yorick.BuildAdvisor.1.0"

[Run]
Filename: "{app}\YorickBuildAdvisor.exe"; Description: "Launch Yorick Build Advisor"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-Command ""Stop-Process -Name YorickBuildAdvisor -Force -ErrorAction SilentlyContinue"""; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\YorickBuildAdvisor.exe.WebView2"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Remove old Start Menu shortcut if it exists from dev installs
    DeleteFile(ExpandConstant('{userappdata}\Microsoft\Windows\Start Menu\Programs\Yorick Build Advisor.lnk'));
  end;
end;
