#!/bin/bash

echo "🚀 FileFerry Slack React Frontend - Quick Start"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js version: $(node --version)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.11+ from https://www.python.org/"
    exit 1
fi
echo "✅ Python version: $(python3 --version)"

echo ""
echo "📦 Installing Frontend Dependencies..."
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Frontend installation failed"
        exit 1
    fi
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file..."
    cat > .env << EOF
VITE_API_URL=http://localhost:8000/api
VITE_DEBUG=true
EOF
    echo "✅ .env file created"
fi

cd ..

echo ""
echo "📦 Installing Backend Dependencies..."

# Check if FastAPI is installed
if ! pip show fastapi &> /dev/null; then
    pip install fastapi uvicorn python-multipart
    echo "✅ Backend dependencies installed"
else
    echo "✅ Backend dependencies already installed"
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "To start the application:"
echo ""
echo "  1. Start Backend API (in one terminal):"
echo "     cd src/slack_bot"
echo "     python slack_api.py"
echo ""
echo "  2. Start Frontend UI (in another terminal):"
echo "     cd frontend"
echo "     npm run dev"
echo ""
echo "  3. Open browser:"
echo "     http://localhost:5173"
echo ""
echo "📚 Documentation: frontend/README.md"
echo ""
