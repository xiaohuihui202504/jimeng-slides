@echo off
REM Banana Slides Backend Startup Script for Windows

echo ╔══════════════════════════════════════╗
echo ║   🍌 Banana Slides API Server 🍌   ║
echo ╚══════════════════════════════════════╝
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo ✅ .env file created. Please edit it with your API keys.
    echo.
)

REM Check if virtual environment exists
if not exist venv (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created.
    echo.
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create instance folder if not exists
if not exist instance mkdir instance
if not exist uploads mkdir uploads

echo.
echo ✅ Setup complete!
echo.
echo 🚀 Starting server...
echo.

REM Run the application
python app.py

