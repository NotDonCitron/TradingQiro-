#!/bin/bash
# =============================================================================
# SIGNAL PROCESSOR - BASH ONLY
# Verarbeitet Telegram Signals komplett ohne Python
# =============================================================================

set -e

# Konfiguration aus Environment
BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
TARGET_GROUP="${OWN_GROUP_CHAT_ID}"
REDIS_HOST="${REDIS_HOST:-redis}"

# Funktionen
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

send_telegram_message() {
    local chat_id="$1"
    local message="$2"
    
    curl -s -X POST \
        "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": \"${chat_id}\",
            \"text\": \"${message}\",
            \"parse_mode\": \"Markdown\"
        }" > /dev/null
    
    echo $?
}

is_signal() {
    local message="$1"
    
    # Einfache Signal-Erkennung
    if echo "$message" | grep -q "🟢.*Long\|🟢.*Short"; then
        return 0
    fi
    
    if echo "$message" | grep -q "💸.*USDT\|Target.*Done"; then
        return 0
    fi
    
    return 1
}

parse_signal() {
    local message="$1"
    
    # Extrahiere Symbol
    local symbol=$(echo "$message" | grep -o "[A-Z0-9]\+/USDT" | head -1)
    
    # Extrahiere Direction
    local direction=""
    if echo "$message" | grep -q "🟢.*Long"; then
        direction="LONG"
    elif echo "$message" | grep -q "🟢.*Short"; then
        direction="SHORT"
    fi
    
    # Extrahiere Entry Price
    local entry_price=$(echo "$message" | grep -A1 "Entry price" | tail -1 | grep -o "[0-9]\+\.[0-9]\+")
    
    # Format Signal
    if [ -n "$symbol" ] && [ -n "$direction" ] && [ -n "$entry_price" ]; then
        echo "🎯 **SIGNAL DETECTED**

📈 **${direction}** ${symbol}
💰 **Entry:** ${entry_price}

📊 Original Signal:
${message}"
    else
        # Fallback - original message
        echo "$message"
    fi
}

# Hauptverarbeitungsloop
main() {
    log "🚀 Signal Processor started (bash version)"
    log "📤 Target Group: ${TARGET_GROUP}"
    log "🔗 Redis Host: ${REDIS_HOST}"
    
    while true; do
        # Message aus Redis Queue holen
        message_data=$(redis-cli -h "$REDIS_HOST" BRPOP telegram_messages 1 2>/dev/null | tail -1)
        
        if [ -n "$message_data" ] && [ "$message_data" != "(nil)" ]; then
            log "📨 Processing message..."
            
            # Parse JSON (einfach mit jq)
            if command -v jq >/dev/null 2>&1; then
                message_text=$(echo "$message_data" | jq -r '.text // empty')
                chat_id=$(echo "$message_data" | jq -r '.chat_id // empty')
            else
                # Fallback ohne jq
                message_text=$(echo "$message_data" | cut -d'"' -f4)
                chat_id="-1002299206473"  # Hardcoded VIP Group
            fi
            
            if [ -n "$message_text" ]; then
                # Prüfe ob Signal
                if is_signal "$message_text"; then
                    log "✅ Signal detected, forwarding..."
                    
                    # Parse und formatiere Signal
                    formatted_signal=$(parse_signal "$message_text")
                    
                    # Sende Signal
                    result=$(send_telegram_message "$TARGET_GROUP" "$formatted_signal")
                    
                    if [ "$result" -eq 0 ]; then
                        log "✅ Signal forwarded successfully"
                    else
                        log "❌ Signal forwarding failed"
                    fi
                else
                    log "ℹ️  Not a signal, skipping"
                fi
            fi
        fi
        
        # Kurze Pause
        sleep 1
    done
}

# Signal Handler für graceful shutdown
trap 'log "🛑 Signal Processor stopping..."; exit 0' SIGTERM SIGINT

# Start
main