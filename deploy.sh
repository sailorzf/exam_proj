#!/bin/bash
# Exam System Deployment & Management Script
# Usage: ./deploy.sh [action]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
DATA_DIR="$SCRIPT_DIR/data"
VENV_DIR="$SCRIPT_DIR/venv"
# Detect OS
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    VENV_PYTHON="$VENV_DIR/Scripts/python.exe"
    VENV_PIP="$VENV_DIR/Scripts/pip.exe"
fi
BACKEND_PORT=8000
FRONTEND_PORT=5173
PID_DIR="$SCRIPT_DIR/.pids"
SERVICE_NAME_BACKEND="exam-backend"
SERVICE_NAME_FRONTEND="exam-frontend"

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
    echo "  setup            Install system dependencies (Python 3.12+, Node.js 18+)"
    echo "  install          Install project dependencies (venv + npm)"
    echo "  build            Build frontend for production"
    echo "  start            Start both backend and frontend"
    echo "  stop             Stop both backend and frontend"
    echo "  restart          Restart both backend and frontend"
    echo "  status           Show service running status"
    echo "  prod             Start production mode (PRODUCTION=1)"
    echo "  backup           Backup database"
    echo "  restore          Restore database from latest backup"
    echo ""
    echo -e "${YELLOW}Service Management (systemd):${NC}"
    echo "  svc-install      Install backend/frontend as systemd services"
    echo "  svc-start        Start services via systemd"
    echo "  svc-stop         Stop services via systemd"
    echo "  svc-restart      Restart services via systemd"
    echo "  svc-status       Show systemd service status"
    echo "  svc-uninstall    Remove systemd services"
    echo "  svc-log [name]   View service logs (backend/frontend)"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  ./deploy.sh setup          # First-time: install Python & Node.js"
    echo "  ./deploy.sh install        # Install venv & npm deps"
    echo "  ./deploy.sh start          # Dev mode (nohup)"
    echo "  ./deploy.sh svc-install    # Install as system services"
    echo "  ./deploy.sh svc-start      # Start via systemd"
    echo "  ./deploy.sh svc-log backend  # View backend logs"
}

log_info()  { echo -e "${CYAN}$1${NC}"; }
log_ok()    { echo -e "${GREEN}$1${NC}"; }
log_warn()  { echo -e "${YELLOW}$1${NC}"; }
log_error() { echo -e "${RED}$1${NC}"; }

mkdir -p "$PID_DIR"

# ─── Detect Package Manager ─────────────────────────────
detect_pkg_manager() {
    if command -v apt-get &>/dev/null; then
        echo "apt"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v yum &>/dev/null; then
        echo "yum"
    elif command -v apk &>/dev/null; then
        echo "apk"
    elif command -v zypper &>/dev/null; then
        echo "zypper"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    else
        echo ""
    fi
}

pkg_install() {
    local mgr=$1; shift
    case "$mgr" in
        apt)   apt-get update && apt-get install -y "$@" ;;
        dnf)   dnf install -y "$@" ;;
        yum)   yum install -y "$@" ;;
        apk)   apk add --no-cache "$@" ;;
        zypper) zypper install -y "$@" ;;
        pacman) pacman -S --noconfirm --needed "$@" ;;
    esac
}

# ─── Setup (install Python + Node.js) ────────────────────
do_setup() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "Must run as root (sudo ./deploy.sh setup)"
        exit 1
    fi

    local mgr
    mgr="$(detect_pkg_manager)"
    if [ -z "$mgr" ]; then
        log_error "Unsupported package manager. Please install manually:"
        log_error "  Python 3.12+"
        log_error "  Node.js 18+"
        exit 1
    fi
    log_info "Detected package manager: $mgr"

    # ── Python ────────────────────────────────────────────
    if command -v python3 &>/dev/null; then
        local py_ver
        py_ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local major minor
        major=$(echo "$py_ver" | cut -d. -f1)
        minor=$(echo "$py_ver" | cut -d. -f2)
        if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; }; then
            log_ok "Python $py_ver already installed"
        else
            log_warn "Python $py_ver found, need 3.12+. Installing..."
            if [ "$mgr" = "apt" ]; then
                pkg_install "$mgr" software-properties-common
                add-apt-repository -y ppa:deadsnakes/ppa
                pkg_install "$mgr" python3.12 python3.12-venv python3.12-dev python3-pip curl
            elif [ "$mgr" = "dnf" ] || [ "$mgr" = "yum" ]; then
                pkg_install "$mgr" python3.12 python3.12-pip curl
            else
                pkg_install "$mgr" python3 python3-pip curl
            fi
            # Verify
            python3 --version 2>/dev/null || python3.12 --version 2>/dev/null
        fi
    else
        log_info "Python not found, installing..."
        if [ "$mgr" = "apt" ]; then
            pkg_install "$mgr" software-properties-common
            add-apt-repository -y ppa:deadsnakes/ppa
            pkg_install "$mgr" python3.12 python3.12-venv python3.12-dev python3-pip curl
        elif [ "$mgr" = "dnf" ] || [ "$mgr" = "yum" ]; then
            pkg_install "$mgr" python3.12 python3.12-pip curl
        else
            pkg_install "$mgr" python3 python3-pip curl
        fi
    fi

    # Ensure python3 links to 3.12+ if 3.12 was installed via deadsnakes
    if command -v python3.12 &>/dev/null && ! python3 -c "import sys; exit(0 if sys.version_info >= (3,12) else 1)" 2>/dev/null; then
        log_warn "Setting python3 -> python3.12 (system python3 is older)"
        update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100 2>/dev/null || true
    fi

    # ── Node.js ───────────────────────────────────────────
    local need_node=true
    if command -v node &>/dev/null; then
        local node_ver
        node_ver=$(node -v | sed 's/v//')
        local major_v
        major_v=$(echo "$node_ver" | cut -d. -f1)
        if [ "$major_v" -ge 18 ]; then
            log_ok "Node.js $node_ver already installed"
            need_node=false
        else
            log_warn "Node.js $node_ver found, need 18+. Installing..."
        fi
    fi

    if $need_node; then
        log_info "Installing Node.js 18+ via NodeSource..."
        if command -v curl &>/dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>/dev/null || {
                # Fallback: try system package
                log_warn "NodeSource setup failed, falling back to system package..."
                if [ "$mgr" = "apt" ]; then
                    pkg_install "$mgr" nodejs npm
                elif [ "$mgr" = "dnf" ]; then
                    pkg_install "$mgr" nodejs npm
                else
                    pkg_install "$mgr" nodejs npm
                fi
            }
            # If NodeSource succeeded, install from its repo
            if command -v node &>/dev/null; then
                local nver
                nver=$(node -v | sed 's/v//')
                if [ "$(echo "$nver" | cut -d. -f1)" -ge 18 ]; then
                    log_ok "Node.js $nver installed"
                else
                    pkg_install "$mgr" nodejs
                fi
            else
                pkg_install "$mgr" nodejs
            fi
        else
            pkg_install "$mgr" curl
            curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
            pkg_install "$mgr" nodejs
        fi
    fi

    # ── Install essential build tools ─────────────────────
    if [ "$mgr" = "apt" ]; then
        pkg_install "$mgr" build-essential || true
    fi

    log_ok ""
    log_ok "=== System dependencies installed ==="
    python3 --version 2>/dev/null || python3.12 --version
    node -v 2>/dev/null || log_warn "Node.js not found after install"
    npm -v 2>/dev/null || log_warn "npm not found after install"
}

# ─── Virtual Environment ─────────────────────────────────
ensure_venv() {
    if [ ! -f "$VENV_PYTHON" ]; then
        log_info "Creating Python virtual environment in venv/ ..."
        python3 -m venv "$VENV_DIR"
        log_ok "  Virtual environment created."
    fi
}

# ─── Install ─────────────────────────────────────────────
do_install() {
    ensure_venv

    log_info "Installing backend dependencies (venv)..."
    "$VENV_PIP" install -r "$BACKEND_DIR/requirements.txt"
    log_ok "  Backend dependencies installed."

    log_info "Installing frontend dependencies..."
    if ! command -v npm &>/dev/null; then
        log_error "npm not found. Please install Node.js 18+ first."
        exit 1
    fi
    (cd "$FRONTEND_DIR" && npm install)
    log_ok "  Frontend dependencies installed."
}

# ─── Build ───────────────────────────────────────────────
do_build() {
    log_info "Building frontend for production..."
    (cd "$FRONTEND_DIR" && npm run build)
    log_ok "Build complete: $FRONTEND_DIR/dist/"
}

# ─── Port helpers ────────────────────────────────────────
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

# ─── Start Backend ───────────────────────────────────────
start_backend() {
    log_info "=== Starting backend (port $BACKEND_PORT) ==="
    if is_port_open $BACKEND_PORT; then
        log_warn "  Backend already running on port $BACKEND_PORT"
        return 0
    fi

    ensure_venv
    mkdir -p "$SCRIPT_DIR/logs"

    cd "$BACKEND_DIR"
    nohup "$VENV_PYTHON" -m uvicorn main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload \
        > "$SCRIPT_DIR/logs/backend.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_DIR/backend.pid"
    log_info "  Backend PID: $pid"

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

# ─── Start Frontend ──────────────────────────────────────
start_frontend() {
    log_info "=== Starting frontend (port $FRONTEND_PORT) ==="
    if is_port_open $FRONTEND_PORT; then
        log_warn "  Frontend already running on port $FRONTEND_PORT"
        return 0
    fi

    rm -rf "$FRONTEND_DIR/node_modules/.vite"
    mkdir -p "$SCRIPT_DIR/logs"

    cd "$FRONTEND_DIR"
    nohup npx vite --port $FRONTEND_PORT \
        > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_DIR/frontend.pid"
    log_info "  Frontend PID: $pid"

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

# ─── Stop Backend ────────────────────────────────────────
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
    kill_port $BACKEND_PORT
    log_ok "Backend stopped."
}

# ─── Stop Frontend ───────────────────────────────────────
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
    kill_port $FRONTEND_PORT
    pkill -f "npx.*vite" 2>/dev/null || true
    pkill -f "vite.*$FRONTEND_PORT" 2>/dev/null || true
    log_ok "Frontend stopped."
}

# ─── Services ────────────────────────────────────────────
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

# ─── Production ──────────────────────────────────────────
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

    stop_backend
    kill_port $BACKEND_PORT
    sleep 1

    export PRODUCTION=1
    cd "$BACKEND_DIR"
    nohup "$VENV_PYTHON" -m uvicorn main:app \
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

# ─── Backup / Restore ───────────────────────────────────
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

# ─── systemd Service Management ──────────────────────────
svc_install() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "Must run as root (sudo ./deploy.sh svc-install)"
        exit 1
    fi

    ensure_venv
    local real_dir
    real_dir="$(realpath "$SCRIPT_DIR")"
    local venv_real
    venv_real="$(realpath "$VENV_DIR")"

    # Backend service unit
    cat > /etc/systemd/system/${SERVICE_NAME_BACKEND}.service <<SVCEOF
[Unit]
Description=Exam System Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=$real_dir/backend
ExecStart=$venv_real/bin/python -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --workers 1
Restart=always
RestartSec=5
Environment=PRODUCTION=1

[Install]
WantedBy=multi-user.target
SVCEOF

    # Frontend service unit (production: serve static from backend)
    cat > /etc/systemd/system/${SERVICE_NAME_FRONTEND}.service <<SVCEOF
[Unit]
Description=Exam System Frontend (Vite)
After=network.target

[Service]
Type=simple
WorkingDirectory=$real_dir/frontend
ExecStart=/usr/bin/npx vite --host 0.0.0.0 --port $FRONTEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME_BACKEND}
    systemctl enable ${SERVICE_NAME_FRONTEND}

    log_ok ""
    log_ok "=== Services installed and enabled ==="
    log_ok "  Backend: $SERVICE_NAME_BACKEND"
    log_ok "  Frontend: $SERVICE_NAME_FRONTEND"
    log_ok ""
    log_ok "Run 'sudo ./deploy.sh svc-start' to start them."
}

svc_uninstall() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "Must run as root (sudo ./deploy.sh svc-uninstall)"
        exit 1
    fi

    systemctl stop ${SERVICE_NAME_BACKEND} ${SERVICE_NAME_FRONTEND} 2>/dev/null || true
    systemctl disable ${SERVICE_NAME_BACKEND} ${SERVICE_NAME_FRONTEND} 2>/dev/null || true
    rm -f /etc/systemd/system/${SERVICE_NAME_BACKEND}.service
    rm -f /etc/systemd/system/${SERVICE_NAME_FRONTEND}.service
    systemctl daemon-reload

    log_ok "Services removed."
}

svc_start() {
    systemctl start ${SERVICE_NAME_BACKEND} ${SERVICE_NAME_FRONTEND}
    log_ok "Services started."
}

svc_stop() {
    systemctl stop ${SERVICE_NAME_BACKEND} ${SERVICE_NAME_FRONTEND}
    log_ok "Services stopped."
}

svc_restart() {
    systemctl restart ${SERVICE_NAME_BACKEND} ${SERVICE_NAME_FRONTEND}
    log_ok "Services restarted."
}

svc_status() {
    systemctl status ${SERVICE_NAME_BACKEND} ${SERVICE_NAME_FRONTEND} --no-pager
}

svc_log() {
    local target="${1:-backend}"
    if [ "$target" = "backend" ]; then
        journalctl -u ${SERVICE_NAME_BACKEND} -f --no-pager
    elif [ "$target" = "frontend" ]; then
        journalctl -u ${SERVICE_NAME_FRONTEND} -f --no-pager
    else
        log_error "Unknown service: $target (use 'backend' or 'frontend')"
        exit 1
    fi
}

# ─── Main ────────────────────────────────────────────────
ACTION="${1:-help}"

case "$ACTION" in
    setup)            do_setup ;;
    start)            do_start ;;
    stop)             do_stop ;;
    restart)          do_restart ;;
    status)           do_status ;;
    install)          do_install ;;
    build)            do_build ;;
    prod)             do_prod ;;
    backup)           do_backup ;;
    restore)          do_restore ;;
    svc-install)      svc_install ;;
    svc-uninstall)    svc_uninstall ;;
    svc-start)        svc_start ;;
    svc-stop)         svc_stop ;;
    svc-restart)      svc_restart ;;
    svc-status)       svc_status ;;
    svc-log)          svc_log "${2:-backend}" ;;
    help|-h|--help)   show_help ;;
    *)                log_error "Unknown action: $ACTION"; show_help; exit 1 ;;
esac
