REM also pm copied from syt -_-

@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SFM_PY=%SCRIPT_DIR%sfm.py"
set "SCRIPT_DIR_CLEAN=%SCRIPT_DIR:~0,-1%"

if not exist "%SFM_PY%" (
    echo Error: sfm.py not found in %SCRIPT_DIR%
    exit /b 1
)

echo.
echo   installing sfm... hold tight! :3
echo.

set "WRAPPER=%SCRIPT_DIR%sfm.bat"
(
    echo @echo off
    echo where py ^>nul 2^>^&1
    echo if %%errorlevel%%==0 ^(
    echo   py -3 "%SFM_PY%" %%*
    echo ^) else ^(
    echo   python "%SFM_PY%" %%*
    echo ^)
) > "%WRAPPER%"

set "PS_WRAPPER=%SCRIPT_DIR%sfm.ps1"
(
    echo if (Get-Command py -ErrorAction SilentlyContinue^) { py -3 "%SFM_PY%" @args } else { python "%SFM_PY%" @args }
) > "%PS_WRAPPER%"

echo %PATH% | findstr /i /c:"%SCRIPT_DIR_CLEAN%" >nul 2>&1
if errorlevel 1 (
    echo   Adding %SCRIPT_DIR_CLEAN% to user PATH...
    set "PS_CMD=$user=[Environment]::GetEnvironmentVariable('Path','User');$dir='%SCRIPT_DIR_CLEAN%';if([string]::IsNullOrWhiteSpace($user)){$new=$dir}else{$parts=$user -split ';';if($parts -contains $dir){$new=$user}else{$new=$user+';'+$dir}};[Environment]::SetEnvironmentVariable('Path',$new,'User')"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "%PS_CMD%" >nul 2>&1
    if errorlevel 1 (
        echo   Could not update PATH automatically.
        echo   Manually add this to your PATH: %SCRIPT_DIR_CLEAN%
    ) else (
        echo   PATH updated. Restart your terminal.
    )
)

echo   Installing Python dependencies...
echo.

py -3 -m pip install --quiet rembg Pillow requests trafilatura 2>nul ^
    || python -m pip install --quiet rembg Pillow requests trafilatura 2>nul ^
    || (
        echo.
        echo   WARNING: pip install failed - try manually:
        echo     pip install rembg Pillow requests trafilatura
    )

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo.
    echo   WARNING: ffmpeg not found ^(needed for convert, compress, transcribe^)
    echo     download it from https://ffmpeg.org/download.html
)

where pandoc >nul 2>&1
if errorlevel 1 (
    echo.
    echo   WARNING: pandoc not found ^(needed for doc conversion^)
    echo     download it from https://pandoc.org/installing.html
)

echo.
echo   done! sfm installed to %WRAPPER% :3
echo   restart your terminal, then run:  sfm
echo.
pause