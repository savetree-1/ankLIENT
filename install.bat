@echo off
echo ========================================
echo   Setting up ChatGPT Local (Windows)
echo ========================================
echo.

echo [1/3] Creating virtual environment...
python -m venv .venv

echo [2/3] Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
playwright install chromium

echo [3/3] Creating gpt launcher...
echo @echo off > gpt.bat
echo call "%CD%\.venv\Scripts\activate.bat" >> gpt.bat
echo python "%CD%\app\main.py" %%* >> gpt.bat

echo.
echo ========================================
echo Setup Complete! 
echo To use the 'gpt' command from anywhere, copy the newly created 'gpt.bat' file into C:\Windows
echo Otherwise, just double click gpt.bat to run it!
echo ========================================
pause
