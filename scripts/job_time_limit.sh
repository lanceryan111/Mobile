#!/bin/bash
###############################################################################

# check_runner.sh

# 

# Monitors GitHub Actions runner job duration via cilogs.

# If a job has been running longer than the configured threshold,

# stops and restarts the runner service, and sends an email notification.

# 

# Usage:

# ./check_runner.sh [options]

# Intended to be run via cron every 10 minutes.

# 

# Crontab entry:

# */10 * * * * /path/to/check_runner.sh >> /var/log/check_runner.log 2>&1

# 

# Requirements:

# - cilogs directory with <hostname>.local.txt log file

# - svc.sh in the runner directory for service management

###############################################################################

set -euo pipefail

# ========================== CONFIGURATION ==========================

# Max allowed job duration in seconds (default: 2 hours = 7200s)

MAX_DURATION_SECONDS=”${MAX_DURATION_SECONDS:-7200}”

# Path to cilogs directory

CILOGS_DIR=”${CILOGS_DIR:-$HOME/cilogs}”

# Path to the runner directory where svc.sh lives

RUNNER_DIR=”${RUNNER_DIR:-$HOME/cad-mob-macos}”

# Timeout for svc stop/start operations (seconds)

SVC_TIMEOUT=”${SVC_TIMEOUT:-30}”

# Email notification settings

EMAIL_ENABLED=”${EMAIL_ENABLED:-true}”
EMAIL_TO=”${EMAIL_TO:-your-team@td.com}”
EMAIL_FROM=”${EMAIL_FROM:-runner-watchdog@$(hostname)}”

# ========================== FUNCTIONS ==============================

log() {
echo “[$(date ‘+%Y-%m-%d %H:%M:%S’)] $*”
}

get_hostname() {
# Get the local hostname (matching the format in cilogs)
scutil –get LocalHostName 2>/dev/null || hostname -s
}

get_log_file() {
local host
host=$(get_hostname)
local log_file=”${CILOGS_DIR}/${host}.local.txt”

```
if [[ ! -f "$log_file" ]]; then
    log "ERROR: Log file not found: $log_file"
    exit 1
fi
echo "$log_file"
```

}

send_email_notification() {
local hostname=”$1”
local job_duration_mins=”$2”
local threshold_mins=”$3”
local action=”$4”
local subject=”[Runner Watchdog] Service restarted on ${hostname}”
local body

```
body=$(cat <<EOF
```

# Runner Watchdog Alert

Host:           ${hostname}
Timestamp:      $(date ‘+%Y-%m-%d %H:%M:%S %Z’)
Job Duration:   ${job_duration_mins} minutes
Threshold:      ${threshold_mins} minutes
Action Taken:   ${action}

The GitHub Actions runner service on ${hostname} was automatically
restarted because a job exceeded the maximum allowed duration.

Please verify the runner is healthy.

–
Runner Watchdog (check_runner.sh)
EOF
)

```
if [[ "$EMAIL_ENABLED" != "true" ]]; then
    log "Email notification disabled. Would have sent to: $EMAIL_TO"
    return 0
fi

# Try mailx/mail first, fallback to sendmail
if command -v mailx &>/dev/null; then
    echo "$body" | mailx -s "$subject" -r "$EMAIL_FROM" "$EMAIL_TO"
elif command -v mail &>/dev/null; then
    echo "$body" | mail -s "$subject" "$EMAIL_TO"
elif command -v sendmail &>/dev/null; then
    {
        echo "From: $EMAIL_FROM"
        echo "To: $EMAIL_TO"
        echo "Subject: $subject"
        echo "Content-Type: text/plain; charset=UTF-8"
        echo ""
        echo "$body"
    } | sendmail -t
else
    log "WARNING: No mail command found (mailx/mail/sendmail). Email not sent."
    log "Email body: $body"
    return 1
fi

log "Email notification sent to $EMAIL_TO"
```

}

restart_runner_service() {
local svc_script=”${RUNNER_DIR}/svc.sh”

```
if [[ ! -x "$svc_script" ]]; then
    log "ERROR: svc.sh not found or not executable at: $svc_script"
    return 1
fi

log "Stopping runner service (timeout: ${SVC_TIMEOUT}s)..."
if timeout "$SVC_TIMEOUT" "$svc_script" stop 2>&1; then
    log "Service stopped successfully."
else
    local exit_code=$?
    if [[ $exit_code -eq 124 ]]; then
        log "WARNING: svc.sh stop timed out after ${SVC_TIMEOUT}s"
    else
        log "WARNING: svc.sh stop exited with code $exit_code"
    fi
fi

# Brief pause between stop and start
sleep 2

log "Starting runner service (timeout: ${SVC_TIMEOUT}s)..."
if timeout "$SVC_TIMEOUT" "$svc_script" start 2>&1; then
    log "Service started successfully."
else
    local exit_code=$?
    if [[ $exit_code -eq 124 ]]; then
        log "ERROR: svc.sh start timed out after ${SVC_TIMEOUT}s"
    else
        log "ERROR: svc.sh start exited with code $exit_code"
    fi
    return 1
fi

return 0
```

}

# ========================== MAIN LOGIC =============================

main() {
log “===== Runner Watchdog Check Started =====”

```
local log_file
log_file=$(get_log_file)
log "Reading log file: $log_file"

# Step 2: tail -n 1 to get the last entry
local last_line
last_line=$(tail -n 1 "$log_file")
log "Last entry: $last_line"

# Parse: hostname,epoch_timestamp,status
local host timestamp status
IFS=',' read -r host timestamp status <<< "$last_line"

if [[ -z "$host" || -z "$timestamp" || -z "$status" ]]; then
    log "ERROR: Failed to parse last line: $last_line"
    exit 1
fi

log "Host=$host | Timestamp=$timestamp | Status=$status"

# Step 3: Check if the last status is "start" (job is running)
if [[ "$status" != "start" ]]; then
    log "Last status is '$status' (not 'start'). No active job. Nothing to do."
    log "===== Check Complete ====="
    exit 0
fi

# Step 4: Calculate job duration
local now
now=$(date +%s)
local duration=$(( now - timestamp ))
local duration_mins=$(( duration / 60 ))
local threshold_mins=$(( MAX_DURATION_SECONDS / 60 ))

log "Job started at epoch $timestamp ($(date -r "$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'N/A'))"
log "Current time: epoch $now"
log "Job duration: ${duration_mins} minutes (${duration}s)"
log "Threshold:    ${threshold_mins} minutes (${MAX_DURATION_SECONDS}s)"

# Step 6: If job duration >= threshold, restart service
if [[ $duration -ge $MAX_DURATION_SECONDS ]]; then
    log "⚠️  THRESHOLD EXCEEDED! Job running for ${duration_mins}m >= ${threshold_mins}m limit."
    
    local action_result="UNKNOWN"
    if restart_runner_service; then
        action_result="Service successfully stopped and restarted"
    else
        action_result="Service restart FAILED - manual intervention required"
    fi
    log "Action result: $action_result"

    # Step 8: Send email notification
    send_email_notification "$host" "$duration_mins" "$threshold_mins" "$action_result"
else
    local remaining=$(( MAX_DURATION_SECONDS - duration ))
    local remaining_mins=$(( remaining / 60 ))
    log "Job within threshold. ${remaining_mins}m remaining before action."
fi

log "===== Check Complete ====="
```

}

main “$@”

#!/bin/bash
###############################################################################
# check_runner_jobtime.zsh
# Managed by Ansible - DO NOT EDIT MANUALLY
# Role: runner-watchdog
#
# Monitors GitHub Actions runner job duration via cilogs.
# If a job exceeds the threshold, stops and restarts the runner service,
# then verifies the new process was freshly spawned.
###############################################################################

set -euo pipefail

MAX_DURATION_SECONDS="{{ max_duration_seconds }}"
CILOGS_DIR="{{ cilogs_dir }}"
RUNNER_DIR="{{ runner_dir }}"
SVC_TIMEOUT="{{ svc_timeout }}"
# Wait time between stop and start (seconds)
SVC_RESTART_WAIT="{{ svc_restart_wait | default('150') }}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$(hostname -s)] $*"
}

get_log_file() {
    local host
    host=$(scutil --get LocalHostName 2>/dev/null || hostname -s)
    local log_file="${CILOGS_DIR}/${host}.local.txt"
    if [[ ! -f "$log_file" ]]; then
        log "ERROR: Log file not found: $log_file"
        exit 1
    fi
    echo "$log_file"
}

# Get the PID of the runner listener process
get_runner_pid() {
    pgrep -f "Runner.Listener" 2>/dev/null || echo ""
}

# Check svc status and log it
check_svc_status() {
    local svc_script="${RUNNER_DIR}/svc.sh"
    log "--- Checking svc status ---"
    if "$svc_script" status 2>&1 | while IFS= read -r line; do log "  svc status: $line"; done; then
        return 0
    else
        log "  svc status check returned non-zero"
        return 1
    fi
}

# Verify the runner process was freshly started by checking lstart
verify_fresh_pid() {
    local pid="$1"
    if [[ -z "$pid" ]]; then
        log "ERROR: No runner PID found after restart"
        return 1
    fi

    local lstart
    lstart=$(ps -o lstart= -p "$pid" 2>/dev/null || echo "")
    if [[ -z "$lstart" ]]; then
        log "ERROR: Could not get lstart for PID $pid"
        return 1
    fi

    # Convert lstart to epoch for comparison
    local pid_start_epoch
    pid_start_epoch=$(date -j -f "%c" "$lstart" "+%s" 2>/dev/null || date -d "$lstart" "+%s" 2>/dev/null || echo "0")
    local now
    now=$(date +%s)
    local age=$(( now - pid_start_epoch ))

    log "Runner PID: $pid"
    log "Process started at: $lstart (${age}s ago)"

    # If process started within the last 5 minutes, it's fresh
    if [[ $age -le 300 ]]; then
        log "VERIFIED: PID $pid is freshly spawned (${age}s old)"
        return 0
    else
        log "WARNING: PID $pid appears stale (${age}s old)"
        return 1
    fi
}

restart_runner_service() {
    local svc_script="${RUNNER_DIR}/svc.sh"
    if [[ ! -x "$svc_script" ]]; then
        log "ERROR: svc.sh not found or not executable at: $svc_script"
        return 1
    fi

    # Step 3: Check status before stop
    check_svc_status

    # Record PID before stop
    local old_pid
    old_pid=$(get_runner_pid)
    log "Runner PID before stop: ${old_pid:-none}"

    # Step 4: Stop svc
    log "Stopping runner service (timeout: ${SVC_TIMEOUT}s)..."
    if timeout "$SVC_TIMEOUT" "$svc_script" stop 2>&1; then
        log "Service stopped successfully."
    else
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            log "WARNING: svc.sh stop timed out after ${SVC_TIMEOUT}s"
        else
            log "WARNING: svc.sh stop exited with code $exit_code"
        fi
    fi

    # Step 4: Wait 2-3 minutes before restart
    log "Waiting ${SVC_RESTART_WAIT}s before restart..."
    sleep "$SVC_RESTART_WAIT"

    # Step 5: Start svc
    log "Starting runner service (timeout: ${SVC_TIMEOUT}s)..."
    if timeout "$SVC_TIMEOUT" "$svc_script" start 2>&1; then
        log "Service started successfully."
    else
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            log "ERROR: svc.sh start timed out after ${SVC_TIMEOUT}s"
        else
            log "ERROR: svc.sh start exited with code $exit_code"
        fi
        return 1
    fi

    # Brief wait for process to fully spawn
    sleep 5

    # Step 5: Verify new PID is fresh
    local new_pid
    new_pid=$(get_runner_pid)
    log "Runner PID after start: ${new_pid:-none}"

    if [[ -n "$old_pid" && "$old_pid" == "$new_pid" ]]; then
        log "WARNING: PID unchanged after restart ($old_pid -> $new_pid)"
    fi

    # Check svc status after restart
    check_svc_status

    # Verify process is freshly spawned
    if [[ -n "$new_pid" ]]; then
        verify_fresh_pid "$new_pid"
    else
        log "ERROR: No runner process found after restart"
        return 1
    fi

    return 0
}

# ========================== MAIN LOGIC =============================

main() {
    log "===== Runner Watchdog Check Started ====="

    local log_file
    log_file=$(get_log_file)
    log "Reading log file: $log_file"

    local last_line
    last_line=$(tail -n 1 "$log_file")
    log "Last entry: $last_line"

    local host timestamp status
    IFS=',' read -r host timestamp status <<< "$last_line"

    if [[ -z "$host" || -z "$timestamp" || -z "$status" ]]; then
        log "ERROR: Failed to parse last line: $last_line"
        exit 1
    fi
    log "Host=$host | Timestamp=$timestamp | Status=$status"

    if [[ "$status" != "start" ]]; then
        log "Last status is '$status' (not 'start'). No active job."
        log "===== Check Complete ====="
        exit 0
    fi

    local now
    now=$(date +%s)
    local duration=$(( now - timestamp ))
    local duration_mins=$(( duration / 60 ))
    local threshold_mins=$(( MAX_DURATION_SECONDS / 60 ))

    log "Job duration: ${duration_mins}m (${duration}s) | Threshold: ${threshold_mins}m (${MAX_DURATION_SECONDS}s)"

    if [[ $duration -ge $MAX_DURATION_SECONDS ]]; then
        log "THRESHOLD EXCEEDED! ${duration_mins}m >= ${threshold_mins}m"
        restart_runner_service
    else
        local remaining_mins=$(( (MAX_DURATION_SECONDS - duration) / 60 ))
        log "Job within threshold. ${remaining_mins}m remaining."
    fi

    log "===== Check Complete ====="
}

main "$@"
