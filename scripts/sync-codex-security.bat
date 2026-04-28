@echo off
setlocal

powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync-codex-security.ps1" %*
exit /b %ERRORLEVEL%
