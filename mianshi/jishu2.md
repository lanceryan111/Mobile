各题型的"思路话术"示例
Shell 题（Q1-Q4）：

"我的思路是：输入验证 → 核心处理逻辑 → 输出格式化。核心处理我会用管道串联 grep/awk/sort，流式处理避免内存问题。安全方面我会加路径检查防止误删。"

Python 题（Q5-Q8）：

"我会用面向对象的方式组织代码：一个主类负责逻辑，方法按功能拆分，这样每个检查项可以独立测试和扩展。API 调用部分我会处理分页、超时、和认证。"

GitHub Actions 题（Q9-Q10）：

"我先画出 job 依赖图：build → scan → docker → deploy。关键设计点是：PR 和 merge 走不同路径，scan 用 Pipeline Scan（快）还是 Full Scan（全）取决于触发类型。Secrets 通过 environment 隔离。"

K8s/Docker 题（Q11-Q13）：

"Dockerfile 优化我关注三个维度：体积（multi-stage）、安全（non-root）、构建速度（layer caching）。我先写一个能跑的版本，然后逐项优化。"

Ansible/Terraform 题（Q14-Q15）：

"Playbook 我会按 '安装 → 配置 → 启动 → 验证' 的顺序组织 tasks。关键是用 handlers 实现幂等性——配置没变就不重启服务。"


面试中的节奏控制
整个过程大概这样分配时间（假设一道题15分钟）：
阶段时间做什么说思路1-2分钟分解问题、说方案、提边界情况写代码8-10分钟边写边简短解释关键行总结2-3分钟"如果时间充裕我还会加 X"、回答追问
写代码时不需要每行都解释，只在关键决策点说一句就够了，比如：

(写到错误处理时) "这里我加个 exit 1，这样在 CI pipeline 里可以捕获失败"
(写到并行逻辑时) "用 wait -n 控制并发上限，避免同时打开太多 SSH 连接"

这样面试官全程都能跟上你的思考，即使代码没写完也能给高分。Fei 你平时做 code review 的习惯其实就是这个思维方式，只是面试时要说出来而已。

# TD WebBroker Platform — DevOps Engineer Technical Coding Interview Prep

**Round 2: Coding Questions & Reference Answers**
Prepared: March 2026

---

## Part 1: Shell / Bash 脚本（最高概率）

面试官最可能考的就是实际场景的 Shell 脚本题。WebBroker 团队日常大量使用 Unix Shell、Python、Ansible 做自动化，这是必考项。

---

### Q1: 日志分析脚本

**题目：** 给你一个应用日志文件 app.log，格式如下：

```
2026-03-28 09:15:23 ERROR [TradeService] Connection timeout to DB
2026-03-28 09:15:24 INFO  [AuthService] User login successful
2026-03-28 09:15:25 ERROR [TradeService] Failed to execute order #12345
2026-03-28 09:16:01 WARN  [CacheService] Cache miss ratio exceeds 30%
```

要求：写一个脚本，统计每个服务的 ERROR 数量，按数量降序输出，并显示最近一小时的 error 趋势。

**参考答案：**

```bash
#!/bin/bash
# Usage: ./analyze_errors.sh <logfile> [hours_back]

LOGFILE="${1:?Usage: $0 <logfile> [hours_back]}"
HOURS="${2:-1}"

# Validate input
if [[ ! -f "$LOGFILE" ]]; then
    echo "Error: File $LOGFILE not found" >&2
    exit 1
fi

# 1. Overall ERROR count by service
echo "=== ERROR Count by Service ==="
grep 'ERROR' "$LOGFILE" \
    | awk -F'[][]' '{print $2}' \
    | sort | uniq -c | sort -rn

# 2. Errors in last N hours
CUTOFF=$(date -d "-${HOURS} hours" +"%Y-%m-%d %H:%M:%S" 2>/dev/null \
    || date -v-${HOURS}H +"%Y-%m-%d %H:%M:%S")  # Linux || macOS

echo ""
echo "=== Errors in last ${HOURS} hour(s) ==="
awk -v cutoff="$CUTOFF" '
    $0 ~ /ERROR/ && ($1" "$2) >= cutoff {
        match($0, /\[([^]]+)\]/, svc);
        count[svc[1]]++
    }
    END {
        for (s in count) printf "%5d  %s\n", count[s], s
    }
' "$LOGFILE" | sort -rn

# 3. Error trend by 10-min intervals
echo ""
echo "=== Error Trend (10-min buckets) ==="
grep 'ERROR' "$LOGFILE" \
    | awk '{print substr($2,1,4)"0"}' \
    | uniq -c
```

**面试要点：**
- 先说思路再写代码："我会分三步：grep 过滤 → awk 解析 → sort+uniq 统计"
- 强调错误处理：检查文件存在、参数验证、stderr 输出
- 提到性能考虑：对于 GB 级日志，可以用 awk 一次遍历代替多次 grep | sort
- 加分项：提到可以用 jq 处理 JSON 格式日志，或集成到 cron 定时执行

---

### Q2: 磁盘/资源监控告警脚本

**题目：** 写一个脚本，检查磁盘使用率，当超过阈值时发送告警（写日志 + 发邮件）。并考虑 cron 调度。

**参考答案：**

```bash
#!/bin/bash
# disk_monitor.sh - Monitor disk usage and alert

THRESHOLD="${1:-85}"
ALERT_LOG="/var/log/disk_alerts.log"
MAIL_TO="devops-team@td.com"
HOSTNAME=$(hostname)

check_disk() {
    # df output: Filesystem Size Used Avail Use% Mounted
    df -h --output=target,pcent | tail -n +2 | while read mount usage; do
        pct=${usage%\%}  # Remove % sign
        if (( pct > THRESHOLD )); then
            TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
            MSG="[${TIMESTAMP}] ALERT: ${HOSTNAME} ${mount} at ${usage} (threshold: ${THRESHOLD}%)"

            # Log locally
            echo "$MSG" >> "$ALERT_LOG"

            # Send email (using TD internal SMTP relay)
            echo "$MSG" | mail -s "Disk Alert: ${HOSTNAME} ${mount}" "$MAIL_TO"

            # Optional: also write to syslog for Splunk/ELK pickup
            logger -p local0.warning "$MSG"
        fi
    done
}

check_disk
```

**Cron 配置：**

```bash
# Run every 15 minutes
*/15 * * * * /opt/scripts/disk_monitor.sh 85 >> /var/log/disk_monitor_cron.log 2>&1
```

**面试要点：**
- 提到 TD 环境用 Postfix relay 发邮件（你有实际经验）
- 加分：提到可以拓展成监控 CPU/Memory/inode 的通用脚本
- 加分：提到去重逻辑——避免每15分钟重复告警同一个问题

---

### Q3: 批量服务状态检查与重启

**题目：** 给你一个服务器列表，写脚本 SSH 进去检查某个服务状态，如果 down 了就重启。

**参考答案：**

```bash
#!/bin/bash
# check_service.sh - Check and restart service across servers

SERVERS_FILE="${1:?Usage: $0 <servers_file> <service_name>}"
SERVICE="${2:?Please specify service name}"
SSH_OPTS="-o ConnectTimeout=5 -o StrictHostKeyChecking=no"
MAX_PARALLEL=10

check_and_restart() {
    local server="$1"
    local status

    # Check if server is reachable
    if ! ssh $SSH_OPTS "$server" 'echo ok' &>/dev/null; then
        echo "[UNREACHABLE] $server"
        return 1
    fi

    # Check service status
    status=$(ssh $SSH_OPTS "$server" "systemctl is-active $SERVICE" 2>/dev/null)

    if [[ "$status" != "active" ]]; then
        echo "[DOWN] $server - $SERVICE is $status, restarting..."
        ssh $SSH_OPTS "$server" "sudo systemctl restart $SERVICE"

        # Verify restart
        sleep 3
        status=$(ssh $SSH_OPTS "$server" "systemctl is-active $SERVICE")
        if [[ "$status" == "active" ]]; then
            echo "[RECOVERED] $server - $SERVICE restarted successfully"
        else
            echo "[FAILED] $server - $SERVICE restart failed!" >&2
        fi
    else
        echo "[OK] $server - $SERVICE is running"
    fi
}

# Process servers (parallel with max limit)
while read -r server; do
    [[ -z "$server" || "$server" == \#* ]] && continue
    check_and_restart "$server" &

    # Limit parallel SSH connections
    (( $(jobs -rp | wc -l) >= MAX_PARALLEL )) && wait -n
done < "$SERVERS_FILE"

wait  # Wait for remaining background jobs
echo "Done. Check results above."
```

**面试要点：**
- 强调并行化处理：用 & 后台执行 + wait -n 控制并发数
- 强调安全性：SSH timeout、重启后验证、只用 sudo 重启不用 root
- 加分：提到实际工作中会用 Ansible 而不是手写 SSH 循环，但这个脚本展示了底层原理

---

### Q4: 日志清理与轮转脚本

**题目：** 写一个脚本，删除指定目录下 N 天前的日志文件，保留最近 X 个备份，并记录操作日志。

**参考答案：**

```bash
#!/bin/bash
# log_cleanup.sh - Safe log rotation with retention policy

LOG_DIR="${1:?Usage: $0 <log_dir> [days] [keep_count]}"
DAYS="${2:-30}"
KEEP="${3:-5}"
CLEANUP_LOG="/var/log/cleanup_audit.log"
DRY_RUN="${DRY_RUN:-false}"

# Safety checks
if [[ ! -d "$LOG_DIR" ]]; then
    echo "Error: Directory $LOG_DIR does not exist" >&2
    exit 1
fi

# Prevent accidental deletion of critical paths
case "$LOG_DIR" in
    /|/etc|/var|/home|/usr)
        echo "Error: Refusing to clean critical directory: $LOG_DIR" >&2
        exit 1 ;;
esac

log_action() {
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] $1" | tee -a "$CLEANUP_LOG"
}

log_action "Starting cleanup: dir=$LOG_DIR days=$DAYS keep=$KEEP"

# Find and remove old log files
OLD_FILES=$(find "$LOG_DIR" -name "*.log" -o -name "*.log.gz" | while read f; do
    [[ -f "$f" ]] && find "$f" -mtime +${DAYS} -print
done | sort)

TOTAL=$(echo "$OLD_FILES" | grep -c .)
TO_DELETE=$((TOTAL > KEEP ? TOTAL - KEEP : 0))

if (( TO_DELETE > 0 )); then
    echo "$OLD_FILES" | head -n "$TO_DELETE" | while read file; do
        if [[ "$DRY_RUN" == "true" ]]; then
            log_action "[DRY-RUN] Would delete: $file"
        else
            rm -f "$file" && log_action "Deleted: $file"
        fi
    done
else
    log_action "No files to clean up"
fi

log_action "Cleanup complete. Deleted: $TO_DELETE files"
```

**面试要点：**
- Safety first：路径验证、禁止删 / 等关键目录、DRY_RUN 模式
- 可审计：所有删除操作写日志（金融行业合规要求）
- 加分：提到 logrotate 是更成熟的方案，但脚本展示了自定义逻辑能力

---

## Part 2: Python 自动化（高概率）

---

### Q5: 解析 YAML/JSON 配置并验证

**题目：** 写一个 Python 脚本，验证 Kubernetes Deployment manifest 是否符合团队规范：必须有 resource limits、image tag 不能是 latest、必须有 liveness probe。

**参考答案：**

```python
#!/usr/bin/env python3
"""Validate K8s deployment manifests against team standards."""

import yaml
import sys
import re
from pathlib import Path


class ManifestValidator:
    """Validates K8s deployment manifests."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_file(self, filepath: str) -> bool:
        path = Path(filepath)
        if not path.exists():
            self.errors.append(f"File not found: {filepath}")
            return False

        with open(path) as f:
            docs = list(yaml.safe_load_all(f))

        for doc in docs:
            if doc and doc.get('kind') == 'Deployment':
                self._validate_deployment(doc, filepath)

        return len(self.errors) == 0

    def _validate_deployment(self, dep, filepath):
        name = dep.get('metadata', {}).get('name', 'unknown')
        prefix = f"[{filepath}] {name}"

        spec = dep.get('spec', {}).get('template', {}).get('spec', {})
        containers = spec.get('containers', [])

        if not containers:
            self.errors.append(f"{prefix}: No containers defined")
            return

        for c in containers:
            cname = c.get('name', 'unnamed')
            self._check_image(c, f"{prefix}/{cname}")
            self._check_resources(c, f"{prefix}/{cname}")
            self._check_probes(c, f"{prefix}/{cname}")
            self._check_security(c, f"{prefix}/{cname}")

    def _check_image(self, container, prefix):
        """Image tag must not be latest or missing."""
        image = container.get('image', '')
        if ':' not in image:
            self.errors.append(f"{prefix}: Image has no tag: {image}")
        elif image.endswith(':latest'):
            self.errors.append(f"{prefix}: Image uses :latest tag")

    def _check_resources(self, container, prefix):
        """Must have resource requests and limits."""
        resources = container.get('resources', {})
        if not resources.get('requests'):
            self.errors.append(f"{prefix}: Missing resource requests")
        if not resources.get('limits'):
            self.errors.append(f"{prefix}: Missing resource limits")

    def _check_probes(self, container, prefix):
        """Must have liveness and readiness probes."""
        if not container.get('livenessProbe'):
            self.errors.append(f"{prefix}: Missing livenessProbe")
        if not container.get('readinessProbe'):
            self.warnings.append(f"{prefix}: Missing readinessProbe")

    def _check_security(self, container, prefix):
        """Check security best practices."""
        sc = container.get('securityContext', {})
        if sc.get('runAsRoot', False):
            self.errors.append(f"{prefix}: Container runs as root")
        if not sc.get('readOnlyRootFilesystem'):
            self.warnings.append(f"{prefix}: Root filesystem is writable")

    def report(self):
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"  - {e}")
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  - {w}")
        if not self.errors and not self.warnings:
            print("✅ All validations passed!")

        return len(self.errors) == 0


if __name__ == "__main__":
    validator = ManifestValidator()
    files = sys.argv[1:]
    if not files:
        print("Usage: python validate_manifest.py <file1.yaml> [file2.yaml ...]")
        sys.exit(1)

    for f in files:
        validator.validate_file(f)

    success = validator.report()
    sys.exit(0 if success else 1)
```

**面试要点：**
- 结构清晰：用类封装，每个检查独立方法，可扩展
- 区分 error vs warning：必须项和建议项分开处理
- Exit code：返回非零状态码让 CI pipeline 能捕获失败
- 加分：提到可以集成到 GitHub Actions PR check 中作为 gate

---

### Q6: 调用 REST API 并处理响应

**题目：** 写一个 Python 脚本，调用 GitHub API 获取某个 repo 的所有打开的 PR，筛选出超过 7 天未 merge 的，输出报告。

**参考答案：**

```python
#!/usr/bin/env python3
"""Find stale PRs that have been open for too long."""

import requests
import os
import sys
from datetime import datetime, timezone, timedelta


def get_stale_prs(owner: str, repo: str, days: int = 7) -> list:
    """Fetch open PRs older than N days."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN env var required")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    stale_prs = []
    page = 1
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    while True:
        resp = requests.get(
            f"https://github.td.com/api/v3/repos/{owner}/{repo}/pulls",
            headers=headers,
            params={"state": "open", "per_page": 100, "page": page},
            timeout=30
        )
        resp.raise_for_status()
        prs = resp.json()

        if not prs:
            break

        for pr in prs:
            created = datetime.fromisoformat(
                pr["created_at"].replace("Z", "+00:00"))
            if created < cutoff:
                stale_prs.append({
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": pr["user"]["login"],
                    "created": created.strftime("%Y-%m-%d"),
                    "age_days": (datetime.now(timezone.utc) - created).days,
                    "url": pr["html_url"],
                    "draft": pr.get("draft", False),
                    "labels": [l["name"] for l in pr.get("labels", [])]
                })

        page += 1

    return sorted(stale_prs, key=lambda x: x["age_days"], reverse=True)


def print_report(prs: list, repo: str):
    print(f"\n=== Stale PR Report: {repo} ({len(prs)} PRs) ===\n")
    for pr in prs:
        draft_tag = " [DRAFT]" if pr["draft"] else ""
        labels = ", ".join(pr["labels"]) if pr["labels"] else "none"
        print(f'  #{pr["number"]:>5} | {pr["age_days"]:>3}d | '
              f'{pr["author"]:<20} | {pr["title"][:60]}{draft_tag}')
        print(f'         Labels: {labels}')
        print(f'         URL: {pr["url"]}\n')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="WebBroker")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()

    try:
        prs = get_stale_prs(args.owner, args.repo, args.days)
        print_report(prs, args.repo)
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        sys.exit(1)
```

**面试要点：**
- 分页处理：很多人忘记 GitHub API 默认只返回 30 条
- Token 管理：从环境变量读取，不硬编码
- 错误处理：raise_for_status + try/except + timeout
- 加分：提到可以集成 Slack 通知，每天跑一次提醒团队

---

### Q7: 证书/密钥过期检查

**题目：** 写一个 Python 脚本，检查 SSL 证书的过期时间，如果即将过期（N 天内）则告警。

**参考答案：**

```python
#!/usr/bin/env python3
"""Check SSL certificate expiry for a list of domains."""

import ssl
import socket
from datetime import datetime, timezone
import json


def check_cert_expiry(hostname: str, port: int = 443,
                       warn_days: int = 30) -> dict:
    ctx = ssl.create_default_context()
    result = {
        "hostname": hostname,
        "status": "unknown",
        "days_remaining": None,
        "expiry_date": None,
        "issuer": None
    }

    try:
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        expiry = expiry.replace(tzinfo=timezone.utc)
        days_left = (expiry - datetime.now(timezone.utc)).days

        result["expiry_date"] = expiry.strftime("%Y-%m-%d")
        result["days_remaining"] = days_left
        result["issuer"] = dict(x[0] for x in cert["issuer"]).get(
            'organizationName', 'Unknown')

        if days_left < 0:
            result["status"] = "EXPIRED"
        elif days_left < warn_days:
            result["status"] = "WARNING"
        else:
            result["status"] = "OK"

    except (ssl.SSLError, socket.error) as e:
        result["status"] = "ERROR"
        result["error"] = str(e)

    return result


def check_multiple(domains: list, warn_days: int = 30) -> list:
    results = []
    for domain in domains:
        r = check_cert_expiry(domain, warn_days=warn_days)
        results.append(r)
        icon = {"OK": "✅", "WARNING": "⚠️", "EXPIRED": "❌",
                "ERROR": "❗"}.get(r["status"], "?")
        print(f'{icon} {r["hostname"]:<30} {r["status"]:<10} '
              f'days_left={r["days_remaining"]}  '
              f'expires={r["expiry_date"]}')
    return results


if __name__ == "__main__":
    domains = [
        "webbroker.td.com",
        "api.webbroker.td.com",
        "auth.td.com",
    ]
    results = check_multiple(domains, warn_days=30)

    alerts = [r for r in results
              if r["status"] in ("WARNING", "EXPIRED", "ERROR")]
    if alerts:
        print(f"\n⚠️  {len(alerts)} certs need attention!")
        print(json.dumps(alerts, indent=2))
```

**面试要点：**
- 你做过 AppStore Connect 证书监控迁移，可以结合说
- 输出 JSON 方便集成到监控系统（Prometheus/Grafana）
- 加分：提到可以用 concurrent.futures 并行检查多个域名

---

### Q8: 解析构建日志提取失败原因

**题目：** 给你一段 CI/CD 构建日志，用 Python 正则提取所有 error/failure 信息，分类汇总输出报告。

**参考答案：**

```python
#!/usr/bin/env python3
"""Parse CI/CD build logs and categorize failures."""

import re
import sys
from collections import defaultdict

# Error patterns with categories
ERROR_PATTERNS = [
    (r"OutOfMemoryError|heap space|GC overhead",            "MEMORY"),
    (r"Connection (refused|timeout|reset)",                 "NETWORK"),
    (r"Could not resolve dependencies|artifact.*not found", "DEPENDENCY"),
    (r"COMPILATION ERROR|cannot find symbol|syntax error",  "COMPILE"),
    (r"Test.*FAILED|AssertionError|test failure",           "TEST"),
    (r"permission denied|access denied|unauthorized",       "AUTH"),
    (r"No space left on device|disk full",                  "DISK"),
    (r"timeout|timed out|deadline exceeded",                "TIMEOUT"),
]


def parse_build_log(filepath: str) -> dict:
    results = {
        "errors": defaultdict(list),
        "uncategorized": [],
        "total_lines": 0,
        "error_lines": 0
    }

    error_re = re.compile(
        r'(ERROR|FATAL|FAILURE|Exception|Error\b)', re.IGNORECASE)

    with open(filepath) as f:
        for line_num, line in enumerate(f, 1):
            results["total_lines"] += 1
            line = line.strip()

            if not error_re.search(line):
                continue

            results["error_lines"] += 1
            categorized = False

            for pattern, category in ERROR_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    results["errors"][category].append({
                        "line": line_num,
                        "text": line[:200]
                    })
                    categorized = True
                    break

            if not categorized:
                results["uncategorized"].append({
                    "line": line_num,
                    "text": line[:200]
                })

    return results


def print_report(results: dict, filepath: str):
    print(f"\n=== Build Log Analysis: {filepath} ===")
    print(f"Total lines: {results['total_lines']}")
    print(f"Error lines: {results['error_lines']}")

    if results["errors"]:
        print("\n--- Categorized Errors ---")
        for cat, errs in sorted(results["errors"].items(),
                                 key=lambda x: len(x[1]),
                                 reverse=True):
            print(f"\n[{cat}] ({len(errs)} occurrences)")
            for e in errs[:3]:
                print(f'  L{e["line"]}: {e["text"]}')
            if len(errs) > 3:
                print(f"  ... and {len(errs)-3} more")

    if results["uncategorized"]:
        print(f'\n[UNCATEGORIZED] ({len(results["uncategorized"])})')
        for e in results["uncategorized"][:5]:
            print(f'  L{e["line"]}: {e["text"]}')

    # Suggest root cause
    print("\n--- Likely Root Cause ---")
    if results["errors"]:
        top_cat = max(results["errors"].items(), key=lambda x: len(x[1]))
        print(f"Primary failure category: {top_cat[0]} "
              f"({len(top_cat[1])} errors)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_build_log.py <logfile>")
        sys.exit(1)
    results = parse_build_log(sys.argv[1])
    print_report(results, sys.argv[1])
```

**面试要点：**
- 模式可扩展：ERROR_PATTERNS 列表可以轻松添加新类别
- 提到你在 TD 调试 Gradle OOM、Fastlane build failure 的经验
- 加分：提到可以输出结构化 JSON，集成到 Slack bot 自动通知

---

## Part 3: GitHub Actions / CI/CD（中高概率）

---

### Q9: 设计一个完整的 GitHub Actions Workflow

**题目：** 场景：PR 触发 → build + test → Veracode 扫描 → 条件部署到 dev/staging。手写 YAML。

**参考答案：**

```yaml
name: WebBroker CI/CD Pipeline

on:
  pull_request:
    branches: [main, release/*]
  push:
    branches: [main]

env:
  REGISTRY: nexus.td.com/docker
  IMAGE_NAME: webbroker-api

jobs:
  # ---- Job 1: Build & Test ----
  build-and-test:
    runs-on: [self-hosted, linux, webbroker]
    outputs:
      version: ${{ steps.version.outputs.tag }}
    steps:
      - uses: actions/checkout@v4

      - name: Set version tag
        id: version
        run: |
          if [[ "${{ github.event_name }}" == "push" ]]; then
            echo "tag=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT
          else
            echo "tag=pr-${{ github.event.number }}" >> $GITHUB_OUTPUT
          fi

      - name: Build
        run: mvn clean package -DskipTests

      - name: Unit Tests
        run: mvn test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: target/surefire-reports/

  # ---- Job 2: Security Scan ----
  security-scan:
    needs: build-and-test
    runs-on: [self-hosted, linux, webbroker]
    steps:
      - uses: actions/checkout@v4

      - name: Veracode Scan (Pipeline for PR / Full for merge)
        run: |
          if [[ "${{ github.event_name }}" == "pull_request" ]]; then
            java -jar veracode-pipeline-scan.jar \
              --veracode_api_id "${{ secrets.VERACODE_ID }}" \
              --veracode_api_key "${{ secrets.VERACODE_KEY }}" \
              --file target/*.war \
              --fail_on_severity "Very High, High"
          else
            java -jar veracode-wrapper.jar \
              -action UploadAndScan \
              -vid "${{ secrets.VERACODE_ID }}" \
              -vkey "${{ secrets.VERACODE_KEY }}" \
              -filepath target/*.war \
              -appname "WebBroker-API"
          fi

  # ---- Job 3: Docker Build & Push ----
  docker:
    needs: [build-and-test, security-scan]
    if: github.event_name == 'push'
    runs-on: [self-hosted, linux, webbroker]
    steps:
      - uses: actions/checkout@v4
      - name: Build & push image
        run: |
          TAG=${{ needs.build-and-test.outputs.version }}
          docker build -t $REGISTRY/$IMAGE_NAME:$TAG .
          docker push $REGISTRY/$IMAGE_NAME:$TAG

  # ---- Job 4: Deploy to Dev ----
  deploy-dev:
    needs: docker
    runs-on: [self-hosted, linux, webbroker]
    environment: dev
    steps:
      - uses: actions/checkout@v4
      - name: Deploy via Helm
        run: |
          TAG=${{ needs.build-and-test.outputs.version }}
          helm upgrade --install webbroker-api ./helm/webbroker \
            --namespace webbroker-dev \
            --set image.tag=$TAG \
            --values helm/values-dev.yaml \
            --wait --timeout 5m

      - name: Smoke test
        run: curl -sf https://dev.webbroker.td.com/health || exit 1

  # ---- Job 5: Deploy to Staging (manual approval) ----
  deploy-staging:
    needs: deploy-dev
    runs-on: [self-hosted, linux, webbroker]
    environment:
      name: staging
      # Environment protection rule requires manual approval
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          TAG=${{ needs.build-and-test.outputs.version }}
          helm upgrade --install webbroker-api ./helm/webbroker \
            --namespace webbroker-staging \
            --set image.tag=$TAG \
            --values helm/values-staging.yaml \
            --wait --timeout 5m
```

**面试要点：**
- Job 依赖链：build → security → docker → deploy-dev → deploy-staging
- 条件逻辑：PR 只跑 build+scan，merge 才触发部署
- Environment protection rules：staging 需要审批
- 你的实际经验：提到 self-hosted runner、Nexus 集成、bypass 逻辑

---

### Q10: 修复有 Bug 的 Pipeline YAML

**题目：** 以下 workflow 有多个问题，找出并修复：

```yaml
name: Build Pipeline
on: push

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: mvn clean package
      - name: Set output
        run: echo "::set-output name=jar::target/app.jar"

  test:
    runs-on: ubuntu-latest
    steps:
      - run: mvn test

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Deploying ${{ needs.build.outputs.jar }}"
          kubectl apply -f deploy.yaml
```

**参考答案 —— Bug 列表：**

- **Bug 1 - 缺少 checkout:** build 和 test job 都没有 `actions/checkout`，mvn 无法找到代码
- **Bug 2 - set-output 已废弃:** `::set-output` 在 GitHub Actions 新版已移除，应用 `>> $GITHUB_OUTPUT`
- **Bug 3 - test 无依赖:** test job 没有 `needs: build`，会并行执行，可能在 build 完成前就跑
- **Bug 4 - deploy 缺 test 依赖:** deploy 只 depends on build，应该 `needs: [build, test]`
- **Bug 5 - output 未正确声明:** build job 缺少 `outputs` 声明，deploy 无法引用
- **Bug 6 - kubectl 无认证:** 没有配置 kubeconfig 或 AKS credentials
- **Bug 7 - 无分支过滤:** `on: push` 会对所有分支触发，应限制为 `main/release`
- **Bug 8 - artifact 未传递:** build 和 deploy 在不同 runner，jar 文件不会自动传递

**关键修复点：**

```yaml
# 1. Add checkout to every job
# 2. Use $GITHUB_OUTPUT instead of ::set-output
# 3. Add proper job dependencies: test needs build, deploy needs both
# 4. Declare outputs in build job
# 5. Add branch filter: branches: [main, release/*]
# 6. Use upload-artifact/download-artifact for jar file
# 7. Add kubeconfig setup step before kubectl
```

**面试要点：**
- 这道题考察细节观察力，慢慢找不要急
- 按执行顺序说："我会从上往下检查每个 job"
- 强调你对 GitHub Actions 新旧 API 的熟悉度

---

## Part 4: Kubernetes / Docker（中概率）

---

### Q11: 编写并优化 Dockerfile

**题目：** 给一个 Java 应用写 Dockerfile，然后优化镜像大小和安全性。

**初始版（有问题）：**

```dockerfile
FROM openjdk:17
COPY . /app
WORKDIR /app
RUN mvn clean package
EXPOSE 8080
CMD ["java", "-jar", "target/app.jar"]
```

问题：镜像包含 Maven、源码、全量 JDK，运行时以 root 用户。

**优化版（Multi-stage Build）：**

```dockerfile
# Stage 1: Build
FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /build

# Cache dependencies first (layer caching optimization)
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Then copy source and build
COPY src/ src/
RUN mvn clean package -DskipTests -B

# Stage 2: Runtime (minimal image)
FROM eclipse-temurin:17-jre-alpine

# Security: non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app
COPY --from=builder /build/target/app.jar app.jar

# Security: read-only filesystem where possible
RUN chmod 444 app.jar

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:8080/health || exit 1

ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", \
            "-jar", "app.jar"]
```

**优化要点总结：**
- **Multi-stage build:** 构建环境和运行环境分离，镜像从 ~800MB 减小到 ~200MB
- **Layer caching:** 先 COPY pom.xml 再 COPY src，依赖不变时可缓存
- **Alpine base:** 用 JRE-alpine 而不是完整 JDK
- **Non-root:** 创建专用用户运行应用
- **HEALTHCHECK:** 内置健康检查，Kubernetes 可根据此管理 Pod
- **JVM tuning:** MaxRAMPercentage 让 JVM 适配容器 memory limit

---

### Q12: 排查 Pod 故障

**题目：** 给你 kubectl 输出，分析为什么 Pod 在 CrashLoopBackOff，写出排查命令序列。

**参考答案 —— 系统化排查流程：**

```bash
# Step 1: Check pod status and events
kubectl get pods -n webbroker -o wide
kubectl describe pod <pod-name> -n webbroker
# Focus on: Events, Exit Code, Last State

# Step 2: Check logs (current + previous crash)
kubectl logs <pod-name> -n webbroker
kubectl logs <pod-name> -n webbroker --previous

# Step 3: Check resource pressure
kubectl top pod <pod-name> -n webbroker
kubectl top node

# Step 4: Check if configmap/secret exists
kubectl get configmap -n webbroker
kubectl get secret -n webbroker

# Step 5: Verify image exists and is pullable
kubectl get pod <pod-name> -n webbroker \
    -o jsonpath='{.spec.containers[0].image}'

# Step 6: Interactive debug (if needed)
kubectl run debug --rm -it --image=busybox -n webbroker -- sh
# Inside: check DNS, network connectivity
nslookup db-service.webbroker.svc.cluster.local
wget -qO- http://config-service:8080/health

# Step 7: Check events at namespace level
kubectl get events -n webbroker --sort-by='.lastTimestamp' | tail -20
```

**常见 Exit Code 解读：**
- **Exit 0:** 应用正常退出但不应该退出，检查启动命令和配置
- **Exit 1:** 应用崩溃，查看日志中的 Exception
- **Exit 137:** OOMKilled，增加 memory limit 或优化应用内存使用
- **Exit 139:** Segfault，代码或依赖问题

---

### Q13: 编写 Kubernetes Manifest + Helm Template

**题目：** 为 WebBroker API 写一套完整的 Deployment + Service + Ingress，并用 Helm template 支持多环境。

**参考答案 —— Helm Template (templates/deployment.yaml):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-api
  labels:
    app: {{ .Release.Name }}
    env: {{ .Values.env }}
spec:
  replicas: {{ .Values.replicaCount }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
    spec:
      containers:
        - name: api
          image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: {{ .Values.resources.requests.cpu }}
              memory: {{ .Values.resources.requests.memory }}
            limits:
              cpu: {{ .Values.resources.limits.cpu }}
              memory: {{ .Values.resources.limits.memory }}
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
          envFrom:
            - configMapRef:
                name: {{ .Release.Name }}-config
            - secretRef:
                name: {{ .Release.Name }}-secrets
      {{- if .Values.tolerations }}
      tolerations:
        {{- toYaml .Values.tolerations | nindent 8 }}
      {{- end }}
```

**多环境 values 文件：**

```yaml
# values-dev.yaml
env: dev
replicaCount: 2
resources:
  requests: { cpu: 250m, memory: 512Mi }
  limits: { cpu: 500m, memory: 1Gi }

# values-prod.yaml
env: prod
replicaCount: 5
resources:
  requests: { cpu: 1000m, memory: 2Gi }
  limits: { cpu: 2000m, memory: 4Gi }
```

**面试要点：**
- ConfigMap checksum annotation：确保配置变更时自动触发 rollout
- RollingUpdate 策略：maxSurge=1, maxUnavailable=0 实现零停机
- 多环境管理：通过不同的 values 文件而不是修改 template

---

## Part 5: Ansible / Terraform（中概率）

---

### Q14: 写一个 Ansible Playbook

**题目：** 写一个 Ansible playbook，配置一批 RHEL 服务器：安装包、模板化配置文件、启动服务、设置防火墙规则。

**参考答案：**

```yaml
---
# playbook: configure_webbroker_servers.yml
- name: Configure WebBroker application servers
  hosts: webbroker_servers
  become: yes
  vars:
    app_port: 8080
    app_user: webbroker
    java_version: java-17-openjdk
    config_template: templates/application.yml.j2

  handlers:
    - name: restart webbroker
      systemd:
        name: webbroker
        state: restarted
        daemon_reload: yes

    - name: reload firewalld
      systemd:
        name: firewalld
        state: reloaded

  tasks:
    # 1. Install required packages
    - name: Install Java and dependencies
      yum:
        name:
          - "{{ java_version }}"
          - wget
          - unzip
          - nss
        state: present
      tags: packages

    # 2. Create application user
    - name: Create app user
      user:
        name: "{{ app_user }}"
        system: yes
        shell: /sbin/nologin
        home: /opt/webbroker
        create_home: yes
      tags: user

    # 3. Deploy configuration from template
    - name: Deploy application config
      template:
        src: "{{ config_template }}"
        dest: /opt/webbroker/config/application.yml
        owner: "{{ app_user }}"
        mode: '0640'
        validate: 'java -jar /opt/webbroker/validator.jar %s'
      notify: restart webbroker
      tags: config

    # 4. Deploy systemd service file
    - name: Install systemd service
      template:
        src: templates/webbroker.service.j2
        dest: /etc/systemd/system/webbroker.service
        mode: '0644'
      notify: restart webbroker
      tags: service

    # 5. Configure firewall
    - name: Open application port
      firewalld:
        port: "{{ app_port }}/tcp"
        permanent: yes
        immediate: yes
        state: enabled
      notify: reload firewalld
      tags: firewall

    # 6. Start and enable service
    - name: Ensure webbroker is running
      systemd:
        name: webbroker
        state: started
        enabled: yes
      tags: service

    # 7. Health check
    - name: Wait for application to start
      uri:
        url: "http://localhost:{{ app_port }}/health"
        status_code: 200
      retries: 12
      delay: 5
      register: health_result
      until: health_result.status == 200
      tags: verify
```

**面试要点：**
- Handlers：只在配置变更时才重启，体现幂等性
- Tags：允许只跑部分任务（`ansible-playbook --tags config`）
- Validate：配置文件先验证再部署，避免脱线
- 你的经验：提到 TD 的 macOS runner 配置、Postfix relay 都是用 Ansible 做的

---

### Q15: Terraform 资源定义与 State Drift

**题目：** 写一个简单的 Terraform 配置创建 AKS cluster，并解释如何处理 state drift。

**参考答案 —— Terraform 配置：**

```hcl
# main.tf - AKS Cluster for WebBroker

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "tfstatewebbroker"
    container_name       = "tfstate"
    key                  = "webbroker-aks.tfstate"
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "aks" {
  name     = "rg-webbroker-${var.env}"
  location = var.location
}

resource "azurerm_kubernetes_cluster" "webbroker" {
  name                = "aks-webbroker-${var.env}"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  dns_prefix          = "webbroker-${var.env}"
  kubernetes_version  = var.k8s_version

  default_node_pool {
    name                = "system"
    node_count          = var.node_count
    vm_size             = var.vm_size
    os_disk_size_gb     = 128
    vnet_subnet_id      = var.subnet_id
    enable_auto_scaling = true
    min_count           = var.min_nodes
    max_count           = var.max_nodes
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"   # Azure CNI
    load_balancer_sku = "standard"
    network_policy    = "calico"
  }

  tags = {
    Environment = var.env
    Team        = "WebBroker-Platform"
    ManagedBy   = "Terraform"
  }
}
```

**State Drift 处理策略：**
- **发现 drift:** `terraform plan` 会显示 expected vs actual。CI/CD 中定期跑 plan 检测偏离
- **策略 1 - 以 Terraform 为准:** `terraform apply` 覆盖手动修改，恢复到代码定义状态
- **策略 2 - 导入现有资源:** `terraform import` 把手动创建的资源纳入管理
- **策略 3 - State refresh:** `terraform refresh` 更新 state 但不修改资源
- **预防措施:** 所有变更必须走 PR + terraform plan review，禁止手动修改 Azure portal

**面试要点：**
- Remote backend：用 Azure Storage 存 state，支持团队协作和 locking
- State locking：避免多人同时 apply 冲突
- 加分：提到 terraform workspace 管理多环境，或用目录结构分离

---

## 面试策略总结

### 答题框架：STAR + Code

- **Situation:** 简述场景（10秒）
- **Thinking:** 说出你的思路和方案选择（20秒）
- **Action:** 写代码，边写边解释
- **Result:** 说明如何测试、如何集成到 CI/CD

### 每道题必须包含

- 错误处理（input validation, try/catch, exit codes）
- 日志/可观测性（尤其是金融环境，审计很重要）
- 安全性考虑（non-root, secrets 管理, 最小权限）
- 可扩展性（提到如何改进和自动化）

### 结合 TD 经验的亮点

- **Runner watchdog 系统：** 检测和重启 stuck GitHub Actions runners
- **Postfix email relay：** macOS 上配置 TD 内部 SMTP
- **Fastlane iOS build：** 调试 MyAutoFinance app 构建问题
- **Jenkins → GitHub Actions 迁移：** Ruby AppStore Connect 监控
- **Nexus 集成：** artifact 管理和 proxy 配置
- **Gradle OOM 排查：** Android CI/CD 内存泄漏问题
- **PR auto-merge workflow：** branch protection bypass 逻辑




好，我直接给你一套 **“TD Wealth 这轮最可能出的 10 个 code 题 + 标准答案”**。
我会尽量按 **现场面试风格** 来写，不是纯刷题风格。

重点覆盖：

* Python
* Shell
* GitHub Actions / pipeline YAML
* Kubernetes YAML
* Ansible

---

# 1. Python 解析环境配置

### 题目

Write a Python function to read environment-specific values from a configuration dictionary.

### 示例输入

```python
config = {
    "dev": {"url": "dev.example.com", "replicas": 2},
    "prod": {"url": "prod.example.com", "replicas": 5}
}
```

Return the value for a given environment and key.

### 标准答案

```python
def get_config_value(config, env, key):
    if env not in config:
        raise ValueError(f"Environment '{env}' not found")

    if key not in config[env]:
        raise ValueError(f"Key '{key}' not found in environment '{env}'")

    return config[env][key]


config = {
    "dev": {"url": "dev.example.com", "replicas": 2},
    "prod": {"url": "prod.example.com", "replicas": 5}
}

print(get_config_value(config, "prod", "url"))
```

### 面试时讲法

> I added validation to make the function safer, because in automation scripts invalid environments or missing keys are common failure points.

---

# 2. Python health check 脚本

### 题目

Write a Python script that checks whether a list of URLs returns status code 200.

### 标准答案

```python
import requests

def check_urls(urls):
    results = {}

    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            results[url] = "UP" if response.status_code == 200 else f"DOWN ({response.status_code})"
        except requests.RequestException as e:
            results[url] = f"ERROR ({e})"

    return results


urls = [
    "https://example.com",
    "https://httpbin.org/status/404"
]

for url, status in check_urls(urls).items():
    print(f"{url}: {status}")
```

### 面试时讲法

> This is a simple operational health check script. I included timeout and exception handling, because network calls can fail in real deployment environments.

---

# 3. Python 比较两个 artifact 列表

### 题目

Given two lists of artifacts, find which artifacts are missing in the target environment.

### 标准答案

```python
def find_missing_artifacts(source, target):
    return list(set(source) - set(target))


source = ["service-a:1.0", "service-b:2.1", "service-c:3.0"]
target = ["service-a:1.0", "service-c:3.0"]

print(find_missing_artifacts(source, target))
```

### 加分版

```python
def find_missing_artifacts(source, target):
    source_set = set(source)
    target_set = set(target)
    return sorted(source_set - target_set)
```

### 面试时讲法

> I used sets for efficiency and simplicity. This kind of comparison is common in release validation or deployment drift detection.

---

# 4. Python 更新 image tag

### 题目

Write a function that updates an image tag string from one version to another.

### 示例输入

```python
"my-app:1.0.0"
```

### 标准答案

```python
def update_image_tag(image, new_tag):
    if ":" not in image:
        raise ValueError("Invalid image format")
    image_name = image.split(":")[0]
    return f"{image_name}:{new_tag}"


print(update_image_tag("my-app:1.0.0", "1.0.1"))
```

### 面试时讲法

> This is a simplified version. In production I might use a YAML parser if I’m updating a deployment file, but this shows the core logic clearly.

---

# 5. Shell script 检查 service 是否运行

### 题目

Write a shell script to check whether nginx is running.

### 标准答案

```bash
#!/bin/bash

if systemctl is-active --quiet nginx; then
  echo "nginx is running"
  exit 0
else
  echo "nginx is not running"
  exit 1
fi
```

### 面试时讲法

> I return proper exit codes so the script can also be used in automation pipelines or monitoring jobs.

---

# 6. Shell script 检查端口是否监听

### 题目

Write a shell script to check whether port 8080 is listening.

### 标准答案

```bash
#!/bin/bash

PORT=8080

if netstat -tuln | grep -q ":$PORT "; then
  echo "Port $PORT is listening"
  exit 0
else
  echo "Port $PORT is not listening"
  exit 1
fi
```

### 更现代一点的写法

```bash
#!/bin/bash

PORT=8080

if ss -tuln | grep -q ":$PORT "; then
  echo "Port $PORT is listening"
  exit 0
else
  echo "Port $PORT is not listening"
  exit 1
fi
```

### 面试时讲法

> This can be useful as a quick validation step after deployment or during troubleshooting.

---

# 7. GitHub Actions CI pipeline

### 题目

Write a GitHub Actions workflow that installs dependencies, runs tests, and builds the application.

### 标准答案

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build application
        run: npm run build
```

### 面试时讲法

> This is a basic CI workflow. In production I would probably add caching, artifact upload, and security scanning as separate steps or jobs.

---

# 8. GitHub Actions build → scan → deploy

### 题目

Write a workflow where deployment only happens after build and security scan succeed.

### 标准答案

```yaml
name: Build-Scan-Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: npm ci && npm run build

  security-scan:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - name: Run security scan
        run: echo "Run SonarQube or Veracode here"

  deploy:
    runs-on: ubuntu-latest
    needs: security-scan
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: echo "Deploy application"
```

### 面试时讲法

> I used job dependencies to enforce gating. This ensures deployment only happens after both build and security validation succeed.

---

# 9. Kubernetes Deployment YAML

### 题目

Write a Kubernetes Deployment for an application with 3 replicas and a readiness probe.

### 标准答案

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app
          image: my-app:1.0.0
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
```

### 面试时讲法

> I added a readiness probe so the pod only receives traffic when the application is ready, which is important for safe rolling deployments.

---

# 10. Ansible playbook：安装并启动 nginx

### 题目

Write an Ansible playbook to install nginx and ensure the service is started and enabled.

### 标准答案

```yaml
- name: Install and start nginx
  hosts: web
  become: yes

  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Ensure nginx is running
      service:
        name: nginx
        state: started
        enabled: yes
```

### 面试时讲法

> I used Ansible modules instead of shell commands to keep the playbook idempotent and maintainable.

---

# 11. Ansible 配置文件 + handler（额外送你一题，超高价值）

### 题目

Deploy an nginx configuration file and restart nginx only when the config changes.

### 标准答案

```yaml
- name: Configure nginx
  hosts: web
  become: yes

  tasks:
    - name: Copy nginx config
      copy:
        src: nginx.conf
        dest: /etc/nginx/nginx.conf
        owner: root
        group: root
        mode: '0644'
      notify: Restart nginx

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted
```

### 面试时讲法

> This uses a handler so the service only restarts when the configuration actually changes, which reduces unnecessary restarts and improves stability.

---

# 你最该背熟的 5 个

如果时间很紧，优先背这 5 个：

1. Python 解析 config
2. Python health check
3. GitHub Actions build-test-deploy
4. Kubernetes Deployment
5. Ansible install + handler

---

# 面试现场答题策略

如果他让你现场写，建议你这样开头：

> Let me start with a simple version first, and then I can extend it for production use.

然后写出最小可行版本，再口头补：

* error handling
* retries
* security
* logging
* rollback

这样会更像 senior / lead。

---

# 他们很可能的追问

你写完后，可能会接着问：

### GitHub Actions

* Why use `npm ci` instead of `npm install`?
* How would you add security scanning?
* How would you deploy to different environments?

### Kubernetes

* What is the difference between readiness and liveness probes?
* How would you avoid downtime during deployment?
* How would you expose this app externally?

### Ansible

* Why use modules instead of shell?
* What is idempotency?
* How would you structure this for dev/test/prod?

### Python / Shell

* How would you make this more robust?
* How would you handle retries?
* How would you log failures?

---

如果你愿意，我下一条可以继续给你：

**“这 10 道题对应的 follow-up 追问 + 标准英文回答”**

很好，这一步是**决定你这轮能不能从“能写”变成“offer级表现”**的关键🔥
我帮你把刚才那 10 道题对应的 **高概率 follow-up + 标准英文回答**整理出来。

👉 你只要把这些回答练熟，面试官追问基本都能稳住。

---

# 1️⃣ Python config parsing

### ❓Follow-up

> How would you make this function more robust?

### 🗣️回答

> I would improve robustness by adding proper input validation, handling missing keys or environments gracefully, and possibly using default values.
> I would also add logging instead of just raising exceptions, especially if this script is used in automation pipelines, so failures can be traced easily.

---

# 2️⃣ Python health check

### ❓Follow-up

> How would you improve this script for production use?

### 🗣️回答

> I would add retry logic with exponential backoff to handle transient network issues.
> I would also introduce concurrency using threading or async requests to improve performance when checking many endpoints.
> Additionally, I would integrate logging and possibly send alerts if critical services are down.

---

# 3️⃣ Artifact comparison

### ❓Follow-up

> How would this scale for large datasets?

### 🗣️回答

> I used sets for efficient lookup, which gives us O(1) average time complexity.
> For very large datasets, I would consider streaming or chunking the data instead of loading everything into memory, depending on the use case.

---

# 4️⃣ Update image tag

### ❓Follow-up

> How would you apply this to a real Kubernetes deployment file?

### 🗣️回答

> In a real scenario, I would use a YAML parsing library like PyYAML instead of string manipulation.
> That ensures the structure is preserved and reduces the risk of breaking the file format.

---

# 5️⃣ Shell script（service check）

### ❓Follow-up

> How would you integrate this into a pipeline?

### 🗣️回答

> I would rely on the exit code to determine success or failure, so the pipeline can automatically fail if the service is not running.
> This makes it easy to integrate as a validation step after deployment.

---

# 6️⃣ Shell script（port check）

### ❓Follow-up

> What if this script runs on different environments?

### 🗣️回答

> I would make the script more portable by parameterizing the port and avoiding environment-specific commands when possible.
> I might also add fallback checks or use tools like `nc` or `curl` depending on availability.

---

# 7️⃣ GitHub Actions CI pipeline

### ❓Follow-up

> How would you optimize this pipeline?

### 🗣️回答

> I would add dependency caching to reduce build time, for example using the built-in caching mechanism in GitHub Actions.
> I would also parallelize jobs where possible and only run certain steps based on conditions, such as skipping builds for documentation changes.

---

# 8️⃣ Build → Scan → Deploy pipeline

### ❓Follow-up

> Why is it important to put security scanning before deployment?

### 🗣️回答

> This follows the shift-left security approach, where vulnerabilities are detected early in the pipeline.
> By placing security scanning before deployment, we reduce the risk of introducing insecure code into production environments.

---

# 9️⃣ Kubernetes Deployment

### ❓Follow-up

> What is the difference between readiness and liveness probes?

### 🗣️回答

> Readiness probes determine whether a pod is ready to receive traffic, while liveness probes determine whether a container is still healthy and should be restarted.
> Readiness helps avoid sending traffic to unready pods, while liveness helps recover from failures automatically.

---

### ❓Follow-up 2

> How would you avoid downtime during deployment?

### 🗣️回答

> I would use a rolling update strategy with properly configured maxUnavailable and maxSurge values.
> Combined with readiness probes, this ensures that new pods are ready before old ones are terminated.

---

# 🔟 Ansible playbook（install nginx）

### ❓Follow-up

> Why use Ansible modules instead of shell commands?

### 🗣️回答

> Ansible modules are idempotent, which means running the playbook multiple times results in the same state.
> They are also more structured, easier to maintain, and provide better error handling compared to shell scripts.

---

# 1️⃣1️⃣ Ansible handler（配置变更）

### ❓Follow-up

> Why use handlers instead of restarting the service directly?

### 🗣️回答

> Handlers ensure that the service is only restarted when a change actually occurs.
> This avoids unnecessary restarts, reduces service disruption, and improves overall system stability.

---

# ⭐ 最常见“杀手级追问”（你一定要准备）

---

## ❓

> How would you make this production-ready?

👉 这是最重要的问题

### 🗣️万能回答模板（直接背🔥）

> To make this production-ready, I would add proper error handling, logging, and retry mechanisms.
> I would also consider security aspects such as secrets management and access control.
> Additionally, I would integrate monitoring and alerting to ensure visibility and reliability.

---

# ⭐ 第二个高频追问

## ❓

> What are potential failure points?

### 🗣️回答

> Potential failure points include network issues, invalid configurations, dependency failures, and resource constraints.
> To mitigate these, I would add validation, retries, and proper monitoring.

---

# ⭐ 第三个高频追问

## ❓

> How would you scale this?

### 🗣️回答

> I would scale this by introducing parallel execution where possible, optimizing resource usage, and ensuring the system is stateless if needed.
> For larger systems, I would also consider distributing workloads across multiple nodes or services.

---

# 🎯 面试表现拉开差距的关键

👉 普通候选人：
只写代码

👉 强候选人（你要做到）：

写完后主动说👇

> I would also consider reliability, security, and scalability in a real production system.

---

# 🚀 最后建议（临场策略）

如果你卡住，不要沉默，直接说：

> Let me walk through my thinking.

👉 面试官更看重 **思路，而不是完美代码**

---

如果你愿意，我可以再帮你做一个最后冲刺👇

👉 **“1小时模拟面试（我当面试官问你这些题）”**

这个基本是最接近真实面试的准备方式，会让你这轮成功率明显提高 🚀
