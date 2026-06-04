; Game Calc Platform — NSIS 安装脚本
; 用法: makensis /DVERSION=x.y.z /DAPP_ROOT=..\dist endfield_calculator_setup.nsi

Unicode True
RequestExecutionLevel admin

!define PRODUCT_NAME "Game Calc Platform"
!define PUBLISHER "Calc Framework"

!ifndef VERSION
  !define VERSION "0.0.0"
!endif

!ifndef APP_ROOT
  !define APP_ROOT "..\dist"
!endif

Name "${PRODUCT_NAME} v${VERSION}"
OutFile "..\dist\GameCalcPlatform_Setup_v${VERSION}.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
InstallDirRegKey HKLM "Software\${PUBLISHER}\${PRODUCT_NAME}" ""

; 请求管理员权限
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define LAUNCHER_EXE "Game Calc Platform.exe"

Section "-MainInstall"
  SetOutPath "$INSTDIR"

  ; 复制启动器目录
  File /r "${APP_ROOT}\Game Calc Platform\*.*"

  ; 复制许可文件
  File "${APP_ROOT}\..\LICENSE"
  File "${APP_ROOT}\..\NOTICES.md"
  File "${APP_ROOT}\..\DATA_LICENSE"

  ; 写卸载信息到注册表
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${LAUNCHER_EXE}"
  WriteRegDWord HKLM "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWord HKLM "${UNINSTALL_KEY}" "NoRepair" 1

  ; .calcpack 文件关联
  WriteRegStr HKCR ".calcpack" "" "${PRODUCT_NAME}.calcpack"
  WriteRegStr HKCR "${PRODUCT_NAME}.calcpack" "" "Game Calc Platform 配置包"
  WriteRegStr HKCR "${PRODUCT_NAME}.calcpack\DefaultIcon" "" "$INSTDIR\${LAUNCHER_EXE},0"
  WriteRegStr HKCR "${PRODUCT_NAME}.calcpack\shell\open\command" "" '"$INSTDIR\${LAUNCHER_EXE}" --calcpack "%1"'
  System::Call 'Shell32::SHChangeNotify(i 0x8000000, i 0, i 0, i 0)'
SectionEnd

Section "StartMenuAndDesktop"
  ; 开始菜单
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"

  ; 启动器
  IfFileExists "$INSTDIR\${LAUNCHER_EXE}" 0 +3
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Launch ${PRODUCT_NAME}.lnk" "$INSTDIR\${LAUNCHER_EXE}" "" "$INSTDIR\${LAUNCHER_EXE}" 0

  ; 独立入口（如果存在）
  IfFileExists "$INSTDIR\开发者工具箱.exe" 0 +3
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\开发者工具箱.lnk" "$INSTDIR\开发者工具箱.exe" "" "$INSTDIR\开发者工具箱.exe" 0

  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\卸载.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

  ; 桌面快捷方式
  IfFileExists "$INSTDIR\${LAUNCHER_EXE}" 0 +2
    CreateShortCut "$DESKTOP\Game Calc Platform.lnk" "$INSTDIR\${LAUNCHER_EXE}" "" "$INSTDIR\${LAUNCHER_EXE}" 0
SectionEnd

Section /o "AddToPath"
  ; 可选：添加安装目录到 PATH（供 devtool.py 等命令行工具使用）
  Push "$INSTDIR"
  Call AddToPath
SectionEnd

Function .onInstSuccess
  MessageBox MB_OK|MB_ICONINFORMATION "${PRODUCT_NAME} v${VERSION} 安装完成！$\n$\n已安装到: $INSTDIR"
FunctionEnd

Section "Uninstall"
  ; 删除安装目录
  RMDir /r "$INSTDIR"

  ; 删除开始菜单
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"

  ; 删除桌面快捷方式
  Delete "$DESKTOP\Game Calc Platform.lnk"

  ; 删除注册表项
  DeleteRegKey HKLM "${UNINSTALL_KEY}"
  DeleteRegKey HKCR ".calcpack"
  DeleteRegKey HKCR "${PRODUCT_NAME}.calcpack"
  System::Call 'Shell32::SHChangeNotify(i 0x8000000, i 0, i 0, i 0)'
SectionEnd

; ─── 辅助函数 ──────────────────────────────────────

Function AddToPath
  Exch $0
  Push $1
  Push $2
  Push $3

  ReadRegStr $1 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"
  StrCpy $2 $1
  StrCpy $3 ""
  DetailPrint "当前 PATH: $1"

  loop:
    StrCmp $2 "" add
    StrCpy $3 $2 1
    StrCmp $3 ";" 0 next
    StrCpy $2 $2 "" 1
    Goto loop
  next:
    StrCpy $3 $2 1024
    StrCmp $3 $0 found
    IntOp $2 $2 + 1024
    StrCmp $2 "" add
    Goto loop

  found:
    DetailPrint "PATH 中已存在 $0，跳过"
    Goto done

  add:
    StrCmp $1 "" 0 prepend_semicolon
    StrCpy $1 "$0"
    Goto write
  prepend_semicolon:
    StrCpy $1 "$1;$0"

  write:
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" $1
    DetailPrint "已添加 $0 到 PATH"

  done:
    Pop $3
    Pop $2
    Pop $1
    Pop $0
FunctionEnd
