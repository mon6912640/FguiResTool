@echo off
set CUR=%~dp0
pyinstaller -D -w -i icon.ico FguiResTool.py
pause