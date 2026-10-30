; Namaz Takip kurulum sihirbazı (Inno Setup 6).
; Derleme: python build_installer.py   (EXE'yi derler, sürümü app/version.py'den alıp bu betiği ISCC ile çalıştırır)
; Elle:    ISCC /DAppVersion=0.1.0 packaging\NamazTakip.iss   (önce dist\NamazTakip\ klasörü derlenmiş olmalı)

#ifndef AppVersion
  #error AppVersion tanımlı değil: ISCC /DAppVersion=X.Y.Z ile ya da build_installer.py ile derleyin.
#endif

#define AppName "Namaz Takip"
#define AppExe "NamazTakip.exe"
#define RepoUrl "https://github.com/Yusufygc/NamazTakip-Desktop"

[Setup]
; AppId sabittir: sonraki sürümler aynı kurulumun üstüne yazılır (güncelleme); ASLA değiştirmeyin.
AppId={{6E2B7C1D-8A44-4F3E-9B05-3D7C5A1E94F2}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Yusufygc
AppPublisherURL={#RepoUrl}
AppSupportURL={#RepoUrl}/issues
AppUpdatesURL={#RepoUrl}/releases
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}
VersionInfoDescription={#AppName} Setup

; Yönetici hakkı gerekmez: varsayılan kullanıcıya özel kurulum (%LOCALAPPDATA%\Programs), sihirbaz "tüm kullanıcılar" seçeneği sunar.
; Kullanıcıya özel kurulum UAC sormaz; uygulama içi güncelleme ve derleme sonrası sessiz deneme bu sayede çalışır.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

; Çalışan uygulama kurulum sırasında kapatılır (güncellemede dosya kilidi olmasın); yeniden açmayı [Run] yapar.
CloseApplications=yes
RestartApplications=no

OutputDir=..\dist\installer
OutputBaseFilename=NamazTakip-Setup-{#AppVersion}
SetupIconFile=..\app\ui\assets\app.ico
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; onedir derlemesi: exe + _internal (Qt DLL'leri, QML, kaynaklar); klasörün tamamı {app}'e.
Source: "..\dist\NamazTakip\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Lisans ve üçüncü taraf bildirimleri uygulamayla birlikte dağıtılır (Qt / LGPL).
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
; Uygulama içi güncelleme (/SILENT) sonrası uygulama kendiliğinden yeniden açılır; derleme sonrası deneme (/VERYSILENT) uygulamayı açmaz.
Filename: "{app}\{#AppExe}"; Flags: nowait; Check: RelaunchAfterUpdate

[Code]
// /VERYSILENT yalnızca derleme sonrası denemede kullanılır (build_verify.py): uygulamayı yeniden açmaz.
function HasParam(const Name: String): Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), Name) = 0 then
    begin
      Result := True;
      Exit;
    end;
end;

function RelaunchAfterUpdate: Boolean;
begin
  Result := WizardSilent and not HasParam('/VERYSILENT');
end;
