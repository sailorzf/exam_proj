#!/bin/bash
# Exam System Deployment & Management Script
# Usage: ./deploy.sh [action]
# Actions: start, stop, restart, status, install, build, prod

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
DATA_DIR="$SCRIPT_DIR/data"
BACKEND_PORT=8000
FRONTEND_PORT=5173
PID_DIR="$SCRIPT_DIR/.pids"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

show_help() {
    echo -e "${CYAN}Exam System Management Script${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC} ./deploy.sh <action>"
    echo ""
    echo -e "${YELLOW}Actions:${NC}"
    echo "  start            Start both backend and frontend"
    echo "  stop             Stop both backend and frontend"
    echo "  restart          Restart both backend and frontend"
    echo "  status           Show service running status"
    echo "  backend-start    Start backend only (port $BACKEND_PORT)"
    echo "  backend-stop     Stop backend only"
    echo "  backend-restart  Restart backend only"
    echo "  frontend-start   Start frontend only (port $FRONTEND_PORT)"
    echo "  frontend-stop    Stop frontend only"
    echo "  frontend-restart Restart frontend only"
    echo "  install          Install all dependencies"
    echo "  build            Build frontend for production"
    echo "  prod             Start production mode (PRODUCTION=1)"
    echo "  backup           Backup database"
    echo "  restore          Restore database from latest backup"
    echo "  help             Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  ./deploy.sh start"
    echo "  ./deploy.sh restart"
    echo "  ./deploy.sh prod"
}

log_info()  { echo -e "${CYAN}$1${NC}"; }
log_ok()    { echo -e "${GREEN}$1${NC}"; }
log_warn()  { echo -e "${YELLOW}$1${NC}"; }
log_error() { echo -e "${RED}$1${NC}"; }

mkdir -p "$PID_DIR"

# ─── Install ───────────────────────────────────────────────
do_install() {
    log_info "Installing backend dependencies..."
    if command -v pip3 &>/dev/null; then
        pip3 install -r "$BACKEND_DIR/requirements.txt"
    elif command -v pip &>/dev/null; then
        pip install -r "$BACKEND_DIR/requirements.txt"
    else
        log_error "pip not found. Please install Python 3.12+ first."
        exit 1
    fi

    log_info "Installing frontend dependencies..."
    if ! command -v npm &>/dev/null; then
        log_error "npm not found. Please install Node.js 18+ first."
        exit 1
    fi
    (cd "$FRONTEND_DIR" && npm install)
    log_ok "All dependencies installed."
}

# ─── Build ─────────────────────────────────────────────────
do_build() {
    log_info "Building frontend for production..."
    (cd "$FRONTEND_DIR" && npm run build)
    log_ok "Build complete: $FRONTEND_DIR/dist/"
}

# ─── Port helpers ──────────────────────────────────────────
kill_port() {
    local port=$1
    local pids
    pids=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        log_warn "  Killing processes on port $port (PIDs: $pids)"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

is_port_open() {
    local port=$1
    lsof -i :$port &>/dev/null
}

# ─── Start Backend ─────────────────────────────────────────
start_backend() {
    log_info "=== Starting backend (port $BACKEND_PORT) ==="
    if is_port_open $BACKEND_PORT; then
        log_warn "  Backend already running on port $BACKEND_PORT"
        return 0
    fi

    cd "$BACKEND_DIR"
    nohup python -m uvicorn main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload \
        > "$SCRIPT_DIR/logs/backend.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_DIR/backend.pid"
    log_info "  Backend PID: $pid"

    # Wait for ready
    printf "  Waiting for backend..."
    for i in $(seq 1 40); do
        if curl -sf "http://127.0.0.1:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
            log_ok " OK"
            return 0
        fi
        printf "."
        sleep 1
    done
    log_error " TIMEOUT"
    return 1
}

# ─── Start Frontend ────────────────────────────────────────
start_frontend() {
    log_info "=== Starting frontend (port $FRONTEND_PORT) ==="
    if is_port_open $FRONTEND_PORT; then
        log_warn "  Frontend already running on port $FRONTEND_PORT"
        return 0
    fi

    # Clean vite cache
    rm -rf "$FRONTEND_DIR/node_modules/.vite"

    cd "$FRONTEND_DIR"
    nohup npx vite --port $FRONTEND_PORT \
        > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_DIR/frontend.pid"
    log_info "  Frontend PID: $pid"

    # Wait for ready
    printf "  Waiting for frontend..."
    for i in $(seq 1 40); do
        if curl -sf "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
            log_ok " OK"
            return 0
        fi
        printf "."
        sleep 1
    done
    log_error " TIMEOUT"
    return 1
}

# ─── Stop Backend ──────────────────────────────────────────
stop_backend() {
    log_info "=== Stopping backend ==="
    if [ -f "$PID_DIR/backend.pid" ]; then
        local pid
        pid=$(cat "$PID_DIR/backend.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
            log_ok "  Stopped PID $pid"
        fi
        rm -f "$PID_DIR/backend.pid"
    fi
    # Fallback: kill by port
    kill_port $BACKEND_PORT
    log_ok "Backend stopped."
}

# ─── Stop Frontend ─────────────────────────────────────────
stop_frontend() {
    log_info "=== Stopping frontend ==="
    if [ -f "$PID_DIR/frontend.pid" ]; then
        local pid
        pid=$(cat "$PID_DIR/frontend.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
            log_ok "  Stopped PID $pid"
        fi
        rm -f "$PID_DIR/frontend.pid"
    fi
    # Fallback: kill by port
    kill_port $FRONTEND_PORT
    # Also kill any remaining vite-related node processes
    pkill -f "npx.*vite" 2>/dev/null || true
    pkill -f "vite.*$FRONTEND_PORT" 2>/dev/null || true
    log_ok "Frontend stopped."
}

# ─── Services ──────────────────────────────────────────────
do_start() {
    mkdir -p "$SCRIPT_DIR/logs"
    stop_backend
    stop_frontend
    sleep 1
    start_backend
    start_frontend
    log_ok ""
    log_ok "=== All services started ==="
    log_ok "  Backend:  http://localhost:$BACKEND_PORT"
    log_ok "  Frontend: http://localhost:$FRONTEND_PORT"
}

do_stop() {
    log_info "=== Stopping all services ==="
    stop_frontend
    stop_backend
    log_ok "All services stopped."
}

do_restart() {
    do_stop
    sleep 2
    do_start
}

do_status() {
    log_info "=== Service Status ==="
    if is_port_open $BACKEND_PORT; then
        log_ok "  Backend ($BACKEND_PORT):  Running"
    else
        log_error "  Backend ($BACKEND_PORT):  Stopped"
    fi
    if is_port_open $FRONTEND_PORT; then
        log_ok "  Frontend ($FRONTEND_PORT): Running"
    else
        log_error "  Frontend ($FRONTEND_PORT): Stopped"
    fi
}

# ─── Production ────────────────────────────────────────────
do_prod() {
    log_info "=== Starting production mode ==="
    mkdir -p "$SCRIPT_DIR/logs"

    if [ -z "$JWT_SECRET_KEY" ]; then
        log_warn "  JWT_SECRET_KEY not set, using default (NOT for production)"
    fi

    if [ ! -d "$FRONTEND_DIR/dist" ]; then
        log_warn "  frontend/dist/ not found, building first..."
        do_build
    fi

    # Kill existing
    stop_backend
    kill_port $BACKEND_PORT
    sleep 1

    export PRODUCTION=1
    cd "$BACKEND_DIR"
    nohup python -m uvicorn main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --workers 1 \
        > "$SCRIPT_DIR/logs/backend-prod.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_DIR/backend.pid"
    log_ok "  Production backend PID: $pid"

    printf "  Waiting for backend..."
    for i in $(seq 1 40); do
        if curl -sf "http://127.0.0.1:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
            log_ok " OK"
            log_ok ""
            log_ok "=== Production mode started ==="
            log_ok "  URL: http://localhost:$BACKEND_PORT"
            log_ok "  Serving frontend from dist/ (PRODUCTION=1)"
            return 0
        fi
        printf "."
        sleep 1
    done
    log_error " TIMEOUT"
    return 1
}

# ─── Backup / Restore ─────────────────────────────────────
do_backup() {
    if [ ! -f "$DATA_DIR/exam.db" ]; then
        log_error "Database not found at $DATA_DIR/exam.db"
        exit 1
    fi
    local ts
    ts=$(date +%Y%m%d_%H%M%S)
    local backup="$DATA_DIR/exam.db.backup.$ts"
    cp "$DATA_DIR/exam.db" "$backup"
    log_ok "Database backed up to $backup"
}

do_restore() {
    local latest
    latest=$(ls -t "$DATA_DIR"/exam.db.backup.* 2>/dev/null | head -1)
    if [ -z "$latest" ]; then
        log_error "No backup found in $DATA_DIR/"
        exit 1
    fi
    log_warn "Restoring from $latest"
    cp "$latest" "$DATA_DIR/exam.db"
    log_ok "Database restored."
}

# ─── Main ──────────────────────────────────────────────────
ACTION="${1:-help}"

case "$ACTION" in
    start)            do_start ;;
    stop)             do_stop ;;
    restart)          do_restart ;;
    status)           do_status ;;
    backend-start)    mkdir -p "$SCRIPT_DIR/logs"; stop_backend; sleep 1; start_backend ;;
    backend-stop)     stop_backend ;;
    backend-restart)  stop_backend; sleep 2; start_backend ;;
    frontend-start)   mkdir -p "$SCRIPT_DIR/logs"; stop_frontend; sleep 1; start_frontend ;;
    frontend-stop)    stop_frontend ;;
    frontend-restart) stop_frontend; sleep 2; start_frontend ;;
    install)          do_install ;;
    build)            do_build ;;
    prod)             do_prod ;;
    backup)           do_backup ;;
    restore)          do_restore ;;
    help|-h|--help)   show_help ;;
    *)                log_error "Unknown action: $ACTION"; show_help; exit 1 ;;
esac
