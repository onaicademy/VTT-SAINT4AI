; VTT @SAINT4AI - Inno Setup Script
; Скрипт для создания Windows инсталлера

#define MyAppName "VTT @SAINT4AI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SAINT4AI"
#define MyAppURL "https://saint4ai.com"
#define MyAppExeName "VTT_SAINT4AI.exe"

[Setup]
; Уникальный ID приложения
AppId={{E8F3A2B1-C5D4-4E6F-9A8B-7C6D5E4F3A2B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\VTT_SAINT4AI
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Права администратора для установки в Program Files
PrivilegesRequired=admin
; Выходной файл
OutputDir=installer_output
OutputBaseFilename=VTT_SAINT4AI_Setup_{#MyAppVersion}
; Сжатие
Compression=lzma2/ultra64
SolidCompression=yes
; Внешний вид
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Запускать при старте Windows"; GroupDescription: "Дополнительно:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Дополнительные файлы если нужны
; Source: "settings.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Автозапуск при старте Windows
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VTT_SAINT4AI"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Проверка что приложение не запущено перед удалением
function InitializeUninstall(): Boolean;
begin
  Result := True;
  // Можно добавить проверку запущенного процесса
end;
