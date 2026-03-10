#!/bin/bash
###############################################################################
# check_runner.sh
# Managed by Ansible - DO NOT EDIT MANUALLY
# Role: runner-watchdog
###############################################################################

set -euo pipefail

MAX_DURATION_SECONDS="{{ max_duration_seconds }}"
CILOGS_DIR="{{ cilogs_dir }}"
RUNNER_DIR="{{ runner_dir }}"
SVC_TIMEOUT="{{ svc_timeout }}"
EMAIL_ENABLED="{{ email_enabled }}"
EMAIL_TO="{{ email_to }}"
EMAIL_FROM="{{ email_from }}"

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

send_email_notification() {
    local hostname="$1"
    local job_duration_mins="$2"
    local threshold_mins="$3"
    local action="$4"
    local subject="[Runner Watchdog] Service restarted on ${hostname}"
    local body
    body=$(cat <<EOF
Runner Watchdog Alert
=====================
Host:           ${hostname}
Timestamp:      $(date '+%Y-%m-%d %H:%M:%S %Z')
Job Duration:   ${job_duration_mins} minutes
Threshold:      ${threshold_mins} minutes
Action Taken:   ${action}

The GitHub Actions runner service on ${hostname} was automatically
restarted because a job exceeded the maximum allowed duration.
EOF
    )

    if [[ "$EMAIL_ENABLED" != "true" ]]; then
        log "Email notification disabled."
        return 0
    fi

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
        log "WARNING: No mail command found. Email not sent."
        return 1
    fi
    log "Email notification sent to $EMAIL_TO"
}

restart_runner_service() {
    local svc_script="${RUNNER_DIR}/svc.sh"
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
}

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

        local action_result="UNKNOWN"
        if restart_runner_service; then
            action_result="Service successfully stopped and restarted"
        else
            action_result="Service restart FAILED - manual intervention required"
        fi
        log "Action result: $action_result"

        send_email_notification "$host" "$duration_mins" "$threshold_mins" "$action_result"
    else
        local remaining_mins=$(( (MAX_DURATION_SECONDS - duration) / 60 ))
        log "Job within threshold. ${remaining_mins}m remaining."
    fi

    log "===== Check Complete ====="
}

main "$@"
