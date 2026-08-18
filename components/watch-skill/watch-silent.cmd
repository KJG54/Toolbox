@echo off
rem Silent launcher for watch-skill: runs the tool with NO console window at all.
rem Use this instead of `watch-skill` directly when you don't want any terminal
rem to flash (e.g. from an agent, a shortcut, or a scheduled task).
rem
rem The tool itself already hides every child process's console window (see
rem watch_skill/proc.py). This wrapper additionally launches the top-level
rem Python with CREATE_NO_WINDOW so even the launcher's own window never
rem appears, and stdout/stderr go to nul so nothing pops.
rem
rem CREATE_NO_WINDOW only — deliberately NOT DETACHED_PROCESS. NO_WINDOW hands
rem the process a window-less console that every descendant inherits; DETACHED
rem leaves it with no console, so each console grandchild allocates a fresh
rem VISIBLE one. Same reasoning as watch_skill/proc.py.
rem
rem Usage:  watch-silent.cmd <url> [question] [extra watch-skill flags...]
rem   (no question -> defaults to a full information-extraction prompt)

set "VENV_PY=%~dp0.venv\Scripts\pythonw.exe"
set "SRC=%~dp0src"

if not exist "%VENV_PY%" (
  echo watch-skill component venv not found at %VENV_PY%
  echo Create the component environment, then use the normal watch-skill command.
  exit /b 1
)

if "%~1"=="" (
  echo Usage: watch-silent.cmd ^<url^> [question] [extra flags...]
  exit /b 1
)

if "%~2"=="" (
  "%VENV_PY%" -c "import sys,subprocess; subprocess.Popen([r'%VENV_PY%','-m','watch_skill.surfaces.cli.main','watch',sys.argv[1],'List every website, tool, product, person, URL, number, and claim shown on screen or spoken in this video, in order, with timestamps'], creationflags=subprocess.CREATE_NO_WINDOW, cwd=r'%SRC%', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)" %1
) else (
  "%VENV_PY%" -c "import sys,subprocess; subprocess.Popen([r'%VENV_PY%','-m','watch_skill.surfaces.cli.main','watch',*sys.argv[1:]], creationflags=subprocess.CREATE_NO_WINDOW, cwd=r'%SRC%', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)" %*
)
exit /b 0
