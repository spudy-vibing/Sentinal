#!/bin/bash
# SENTINEL V2 — Stop Development Servers

echo "Stopping Sentinel V2 development servers..."

# Kill uvicorn processes
pkill -f "uvicorn main:app" 2>/dev/null && echo "Backend stopped" || echo "No backend running"

# Kill vite processes
pkill -f "vite" 2>/dev/null && echo "Frontend stopped" || echo "No frontend running"

echo "Done."
