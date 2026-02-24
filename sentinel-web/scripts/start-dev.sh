#!/bin/bash
# SENTINEL V2 — Development Server Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "  SENTINEL V2 — Starting Development Servers"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Creating .env from template..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "Please edit .env with your ANTHROPIC_API_KEY"
fi

# Start Backend
echo "[1/2] Starting Backend (FastAPI)..."
cd "$PROJECT_DIR/backend"
python3 -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo "      Backend PID: $BACKEND_PID"

# Wait for backend to be ready
sleep 2

# Start Frontend
echo "[2/2] Starting Frontend (Vite)..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "      Frontend PID: $FRONTEND_PID"

echo ""
echo "=============================================="
echo "  Servers Running:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend:  http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop all servers"

# Trap Ctrl+C to kill both processes
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for both processes
wait
