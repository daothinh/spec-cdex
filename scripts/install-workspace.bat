@echo off
setlocal

if "%~1"=="" (
  echo Usage: %~nx0 TARGET_REPO [-Force] [-NoEnablePlugins] [-CodexHome PATH]
  exit /b 1
)

powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-workspace.ps1" %*
exit /b %ERRORLEVEL%
