@echo off
chcp 65001
set save_path=\\192.168.119.6\공유폴더\4. SW\ElroiKit\00. Deploy\Alpha\v1.3.3
set version_path=.\src\
set version_file=version.py

@REM Read Version
for /f "tokens=*" %%l in (%version_path%%version_file%) do (
    for /f "tokens=1,2 delims==' " %%a in ("%%l") do (
        set %%a=%%b
    )
)

@REM Deploy
call iscc .\ElroiKit.iss /Dversion=%major%.%minor%.%patch%.%build_number%.%date:~12,2%%date:~4,2%%date:~7,2%.%maintenance%
copy "Output\ElroiKit_%major%.%minor%.%patch%.%build_number%.%date:~12,2%%date:~4,2%%date:~7,2%.%maintenance%.exe" "%save_path%"