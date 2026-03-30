#!/bin/bash
# find-ports.sh — Detect available ports for ReqStudio services
# Usage: ./scripts/find-ports.sh

set -e

check_port() {
    local port=$1
    if ! (echo > /dev/tcp/localhost/$port) 2>/dev/null; then
        echo "$port"
        return 0
    fi
    return 1
}

find_free_port() {
    local default=$1
    local name=$2
    
    if check_port "$default" > /dev/null 2>&1; then
        echo "$name=$default (default — available)"
    else
        for offset in $(seq 1 100); do
            local candidate=$((default + offset))
            if check_port "$candidate" > /dev/null 2>&1; then
                echo "$name=$candidate (default $default is busy)"
                return
            fi
        done
        echo "$name=NONE (no free port found near $default)"
    fi
}

echo "🔍 Finding available ports for ReqStudio..."
echo ""
echo "# Add these to your .env file:"
find_free_port 8000 "API_PORT"
find_free_port 5432 "DB_PORT"
find_free_port 5173 "FRONTEND_PORT"
echo ""
echo "✅ Done."
