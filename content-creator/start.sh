#!/bin/bash

# AI Content Automation System - Startup Script

echo "Starting AI Content Automation System..."

# Navigate to project directory
cd "$(dirname "$0")"

# Start backend server
echo "Starting backend server on port 8000..."
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 3

# Start frontend development server
echo "Starting frontend development server on port 5173..."
cd web-interface
pnpm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "AI Content Automation System is running!"
echo "========================================"
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT
wait
