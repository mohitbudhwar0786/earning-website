@echo off
echo Starting EarnDaily Website...
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setting up database...
python setup.py

echo.
echo Starting the website...
echo Website will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
