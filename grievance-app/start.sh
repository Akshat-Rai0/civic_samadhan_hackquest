#!/usr/bin/env bash

# Exit immediately if a command fails unexpectedly
set -e

# Resolve project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"

echo "Starting Auto Grievance Raiser..."

# Prepare backend environment
if [ ! -f "${BACKEND_DIR}/.env" ]; then
    echo "Creating backend .env file from .env.example..."
    cp "${BACKEND_DIR}/.env.example" "${BACKEND_DIR}/.env"
fi

# Set up Python virtual environment if not present
if [ ! -d "${BACKEND_DIR}/venv" ]; then
    echo "Creating Python virtual environment in ${BACKEND_DIR}/venv..."
    python3 -m venv "${BACKEND_DIR}/venv"
    "${BACKEND_DIR}/venv/bin/pip" install --upgrade pip
fi

# Ensure backend dependencies are installed
if [ ! -f "${BACKEND_DIR}/venv/bin/uvicorn" ]; then
    echo "Installing backend dependencies in virtual environment..."
    "${BACKEND_DIR}/venv/bin/pip" install -r "${BACKEND_DIR}/requirements.txt"
fi

# Ensure frontend dependencies are installed
if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
    echo "Installing frontend dependencies..."
    (cd "${FRONTEND_DIR}" && npm install)
fi

# Function to clean up background processes on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    if [ -n "${BACKEND_PID}" ]; then
        kill "${BACKEND_PID}" 2>/dev/null || true
    fi
    if [ -n "${FRONTEND_PID}" ]; then
        kill "${FRONTEND_PID}" 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start backend server
echo "Starting backend on http://localhost:8000..."
(
    cd "${BACKEND_DIR}"
    source "${BACKEND_DIR}/venv/bin/activate"
    exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

# Start frontend development server
echo "Starting frontend on http://localhost:3000..."
(
    cd "${FRONTEND_DIR}"
    exec npm run dev -- --host
) &
FRONTEND_PID=$!

echo ""
echo "Both services are running:"
echo "  Citizen Portal & Admin: http://localhost:3000"
echo "  Backend API & Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait for processes
wait
