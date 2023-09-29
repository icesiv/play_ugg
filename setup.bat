@ECHO OFF
ECHO.
ECHO -----------------------------------------------
ECHO Currently configuring project dependencies...
ECHO -----------------------------------------------
ECHO.
ECHO.
cmd /c py -m venv env
cmd /c env\scripts\python.exe -m pip install --upgrade pip
cmd /c env\scripts\python.exe -m pip install -r requirements.txt
cmd /c env\scripts\python.exe -m playwright install
PAUSE