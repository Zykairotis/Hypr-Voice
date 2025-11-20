#!/bin/bash
# Start both frontend and backend for Hypr-Voice Web UI

echo "🚀 Starting Hypr-Voice Web UI..."

# Get the directory of this script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend bridge
echo "📡 Starting backend bridge on port 8934..."
cd "$DIR/api"

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

python bridge.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend
echo "🎨 Starting frontend on port 8933..."
cd "$DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Hypr-Voice Web UI is running!"
echo "   Frontend: http://localhost:8933"
echo "   Backend:  http://localhost:8934"
echo "   API Docs: http://localhost:8934/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait

