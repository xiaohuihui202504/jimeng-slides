#!/bin/bash

# Banana Slides Backend Startup Script

echo "╔══════════════════════════════════════╗"
echo "║   🍌 Banana Slides API Server 🍌   ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your API keys."
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created."
    echo ""
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create instance folder if not exists
mkdir -p instance
mkdir -p uploads

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting server..."
echo ""

# Run the application
python app.py

