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

!ifndef OUTPUT
  !define OUTPUT "..\dist\GameCalcPlatform_Setup_v${VERSION}.exe"
!endif

Name "${PRODUCT_NAME} v${VERSION}"
OutFile "${OUTPUT}"
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

  ; .calcpack 文件关联（仅当未被其他程序占用；记录所有权供卸载恢复）
  ReadRegStr $0 HKCR ".calcpack" ""
  StrCmp $0 "" install_calcpack_assoc
  StrCmp $0 "${PRODUCT_NAME}.calcpack" install_calcpack_assoc
  WriteRegDWord HKLM "${UNINSTALL_KEY}" "CalcpackOwned" 0
  Goto calcpack_assoc_done

  install_calcpack_assoc:
  WriteRegStr HKCR ".calcpack" "" "${PRODUCT_NAME}.calcpack"
  WriteRegStr HKCR "${PRODUCT_NAME}.calcpack" "" "Game Calc Platform 配置包"
  WriteRegStr HKCR "${PRODUCT_NAME}.calcpack\DefaultIcon" "" "$INSTDIR\${LAUNCHER_EXE},0"
  WriteRegStr HKCR "${PRODUCT_NAME}.calcpack\shell\open\command" "" '"$INSTDIR\${LAUNCHER_EXE}" --calcpack "%1"'
  WriteRegDWord HKLM "${UNINSTALL_KEY}" "CalcpackOwned" 1

  calcpack_assoc_done:
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

  ; 删除注册表项（仅当本安装器创建了 .calcpack 关联时才删除）
  ReadRegDWord $0 HKLM "${UNINSTALL_KEY}" "CalcpackOwned"
  DeleteRegKey HKLM "${UNINSTALL_KEY}"
  StrCmp $0 "1" 0 calcpack_uninstall_done
  DeleteRegKey HKCR ".calcpack"
  DeleteRegKey HKCR "${PRODUCT_NAME}.calcpack"

  calcpack_uninstall_done:
  System::Call 'Shell32::SHChangeNotify(i 0x8000000, i 0, i 0, i 0)'
SectionEnd
