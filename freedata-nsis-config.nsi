!include "MUI2.nsh"
!include "LogicLib.nsh"

; Copy a user file from the old install location (next to the executable) to
; %APPDATA%\FreeDATA. Uses BACKUP_NAME if a file of the same name already exists.
!macro MigrateUserFile NAME BACKUP_NAME
  ${If} ${FileExists} "$INSTDIR\freedata-server\${NAME}"
    CreateDirectory "$APPDATA\FreeDATA"
    ${If} ${FileExists} "$APPDATA\FreeDATA\${NAME}"
      CopyFiles /SILENT "$INSTDIR\freedata-server\${NAME}" "$APPDATA\FreeDATA\${BACKUP_NAME}"
    ${Else}
      CopyFiles /SILENT "$INSTDIR\freedata-server\${NAME}" "$APPDATA\FreeDATA\${NAME}"
    ${EndIf}
  ${EndIf}
!macroend

; Version shown in the installer and in "Apps & features".
; CI can pass it with: makensis /DVERSION=x.y.z freedata-nsis-config.nsi
!ifndef VERSION
  !define VERSION "dev"
!endif

!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\FreeDATA"

; Per-user install into %LOCALAPPDATA%, so no administrator rights are needed.
; (Elevating would make $LOCALAPPDATA, $DESKTOP and HKCU point to the admin
; account's profile when a standard user installs with an admin's credentials.)
RequestExecutionLevel user

; The name and file name of the installer
Name "FreeDATA ${VERSION}"
OutFile "FreeDATA-Installer.exe"

; Default installation directory for the server
InstallDir "$LOCALAPPDATA\FreeDATA"

; Registry key to store the installation directory
InstallDirRegKey HKCU "Software\FreeDATA" "Install_Dir"

; Modern UI settings
!define MUI_ABORTWARNING

; Installer interface settings
!define MUI_ICON "documentation\icon.ico"
!define MUI_UNICON "documentation\icon.ico" ; Icon for the uninstaller

; Define the welcome page text
!define MUI_WELCOMEPAGE_TEXT "Welcome to the FreeDATA ${VERSION} Setup Wizard. This wizard will guide you through the installation process."
!define MUI_FINISHPAGE_TEXT "Folder: $INSTDIR"
!define MUI_DIRECTORYPAGE_TEXT_TOP "Please select the installation folder. It's recommended to use the suggested one to avoid permission problems."

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language (you can choose and configure the language(s) you want)
!insertmacro MUI_LANGUAGE "English"


; Installer Sections
Section "FreeDATA Server" SEC01
  SectionIn RO

  ; Versions up to 0.18.1 kept config.ini and the message database next to the
  ; executable. Since 0.18.2 they live in %APPDATA%\FreeDATA
  ; (see freedata_server/constants.py), so move old data there before the old
  ; program folder is removed. Existing data in %APPDATA%\FreeDATA is never
  ; overwritten; the old file is kept beside it as a backup instead.
  !insertmacro MigrateUserFile "config.ini" "config.pre-0.18.2.ini"
  !insertmacro MigrateUserFile "freedata-messages.db" "freedata-messages.pre-0.18.2.db"

  ; Remove files from a previous version so no stale modules are left behind.
  RMDir /r "$INSTDIR\freedata-server"

  SetOutPath "$INSTDIR\freedata-server"
  File /r "freedata_server\server.dist\*"

  ; Uninstaller and "Apps & features" entry
  SetOutPath "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\FreeDATA" "Install_Dir" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "FreeDATA"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "DJ2LS"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "URLInfoAbout" "https://freedata.app"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\freedata-server\freedata-server.exe"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1

  ; Shortcuts: desktop and Start Menu
  CreateShortCut "$DESKTOP\FreeDATA Server.lnk" "$INSTDIR\freedata-server\freedata-server.exe"
  CreateDirectory "$SMPROGRAMS\FreeDATA"
  CreateShortCut "$SMPROGRAMS\FreeDATA\FreeDATA Server.lnk" "$INSTDIR\freedata-server\freedata-server.exe"
  CreateShortCut "$SMPROGRAMS\FreeDATA\Uninstall FreeDATA.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller Section
Section "Uninstall"
  ; Program files only; the user's config, messages and log in
  ; %APPDATA%\FreeDATA are left in place.
  RMDir /r "$INSTDIR\freedata-server"
  Delete "$INSTDIR\Uninstall.exe"
  ; Not recursive: never delete anything else the user put in the chosen folder
  RMDir "$INSTDIR"

  ; Shortcuts
  Delete "$DESKTOP\FreeDATA Server.lnk"
  Delete "$SMPROGRAMS\FreeDATA\FreeDATA Server.lnk"
  Delete "$SMPROGRAMS\FreeDATA\Uninstall FreeDATA.lnk"
  RMDir "$SMPROGRAMS\FreeDATA"

  ; Registry
  DeleteRegKey HKCU "${UNINSTALL_KEY}"
  DeleteRegKey HKCU "Software\FreeDATA"
SectionEnd
