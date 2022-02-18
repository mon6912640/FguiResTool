@echo off
set CUR=%~dp0
pyinstaller -D -i icon.ico FguiResTool.py
pause