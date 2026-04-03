# WebBroker Coding Interview — 15题思路话术速背卡

> **模板：** Confirm → Break → Choose → Risk → Code
>
> 每题控制在 30-40 秒说完 Step 1-4，然后开始写代码。

---

## Q1: 日志分析脚本

**[Confirm]**
"So I need to parse an application log file, count ERROR occurrences by service name, sort by frequency, and show the error trend over the last hour."

**[Break]**
"I'll do this in three steps: first, grep to filter ERROR lines; second, awk to extract the service name from the square brackets; third, sort and uniq to aggregate counts."

**[Choose]**
"I'll use a bash pipeline — grep, awk, sort, uniq — because for line-by-line text processing this is the most efficient approach, no need for Python overhead."

**[Risk]**
"Two things I want to handle: the log file could be very large, so I'll use streaming pipelines instead of loading into memory. Also, the time-based filtering needs to handle different date command syntax between Linux and macOS."

---

## Q2: 磁盘/资源监控告警脚本

**[Confirm]**
"So I need a script that checks disk usage on all mount points, and when any exceeds a threshold, it sends an alert via email and logs the event. It should be cron-schedulable."

**[Break]**
"Three parts: parse df output to get usage percentages per mount point; compare each against the threshold; and for any violations, log locally and send email via SMTP relay."

**[Choose]**
"Pure bash with df and the mail command, since this runs on servers that may not have Python. For email I'll use the internal SMTP relay — I've configured Postfix for this at TD before."

**[Risk]**
"Two edge cases: first, I need deduplication logic so cron doesn't send the same alert every 15 minutes for the same mount. Second, I'll parameterize the threshold so different servers can have different limits."

---

## Q3: 批量服务状态检查与重启

**[Confirm]**
"So given a list of servers, I need to SSH into each, check if a specific service is running, and if it's down, restart it and verify the restart succeeded."

**[Break]**
"Four steps: read the server list; SSH to check service status with systemctl; if down, restart and verify; and I need to handle this in parallel since checking servers sequentially would be too slow."

**[Choose]**
"Bash with background jobs and wait -n for parallelism. In production I'd use Ansible for this, but the script demonstrates the underlying mechanics — SSH, systemctl, error handling."

**[Risk]**
"Three things: SSH timeout — I'll set ConnectTimeout to 5 seconds so one unreachable server doesn't block everything. Max parallel connections — I'll cap at 10 to avoid overwhelming the network. And I'll verify the restart actually worked before reporting success."

---

## Q4: 日志清理与轮转脚本

**[Confirm]**
"So I need to delete log files older than N days from a given directory, keep at least X recent backups, and log all deletion actions for audit."

**[Break]**
"Three parts: safety validation of inputs and paths; find old files with the find command using -mtime; delete them while preserving the minimum backup count, and log every action."

**[Choose]**
"Bash with find -mtime for age-based filtering. I'll add a DRY_RUN mode so we can preview what would be deleted before actually removing anything."

**[Risk]**
"This is a deletion script, so safety is critical. I'll refuse to run on critical paths like / or /etc. I'll add a dry-run mode — especially important in banking where we need audit trails for any file operations. And I'll log every deletion to a separate audit log file."

---

## Q5: 解析 YAML/JSON 配置并验证

**[Confirm]**
"So I need a Python script that validates Kubernetes Deployment manifests against our team standards: resource limits must be set, image tag can't be latest, and liveness probe is required."

**[Break]**
"I'll structure it as: load YAML with safe_load; walk the document tree to find Deployment resources; then run a series of validation checks on each container — image, resources, probes, security context."

**[Choose]**
"Python with PyYAML, using a class-based design. Each check is a separate method so it's easy to add new rules. I'll separate errors from warnings — missing limits is an error, missing readinessProbe is a warning."

**[Risk]**
"I need to handle multi-document YAML files since people often put multiple resources in one file. Also, the exit code matters — returning non-zero so CI pipelines can gate on this. And I'll handle the case where fields are missing entirely, not just wrong values."

---

## Q6: 调用 REST API 并处理响应

**[Confirm]**
"So I need to call the GitHub API to get all open PRs for a repo, filter those older than 7 days, and output a report sorted by age."

**[Break]**
"Three parts: authenticate and paginate through the GitHub API; filter PRs by comparing created_at against our cutoff date; format and output the report with key details like author, age, labels."

**[Choose]**
"Python with the requests library. I'll use pagination because GitHub defaults to 30 results per page — without it we'd miss PRs. Token comes from environment variable, never hardcoded."

**[Risk]**
"Key things: pagination is a must — the API only returns 30 items by default and we could have hundreds of open PRs. I'll add timeout on requests to avoid hanging. And I'll handle rate limiting — GitHub Enterprise has API rate limits that we need to respect."

---

## Q7: 证书/密钥过期检查

**[Confirm]**
"So I need to check SSL certificates for a list of domains and alert if any are expiring within N days."

**[Break]**
"Two parts: connect to each host via SSL, extract the certificate expiry date; then compare against the warning threshold and generate a report with status for each domain."

**[Choose]**
"Python's built-in ssl and socket modules — no external dependencies needed. I'll output both human-readable status and JSON for integration with monitoring systems like Prometheus or Grafana."

**[Risk]**
"Connection failures need graceful handling — a domain might be unreachable or have SSL issues, and that shouldn't crash the whole check. I'll also consider timeout since some hosts might be slow. For production I'd parallelize with concurrent.futures since checking 50+ domains sequentially is slow."

---

## Q8: 解析构建日志提取失败原因

**[Confirm]**
"So given a CI/CD build log, I need to extract all error and failure lines, categorize them by type, and suggest the likely root cause."

**[Break]**
"Three steps: scan each line for error patterns; match against a predefined category map — memory, network, dependency, compile, test failures; then aggregate and report with the most frequent category as the likely root cause."

**[Choose]**
"Python with regex pattern matching. I'll use a list of pattern-to-category tuples that's easy to extend. This design lets the team add new error patterns without changing the core logic."

**[Risk]**
"Build logs can be huge, so I'll process line by line, not load the entire file. I'll truncate very long lines in the output to keep the report readable. And I need an 'uncategorized' bucket for errors that don't match any known pattern — these often reveal new failure modes."

---

## Q9: 设计完整 GitHub Actions Workflow

**[Confirm]**
"So I need a complete CI/CD pipeline: PR triggers build and test, security scan with Veracode, then conditional deployment to dev and staging with approval gates."

**[Break]**
"I'll design five jobs in a dependency chain: build-and-test → security-scan → docker-build → deploy-dev → deploy-staging. The key design decision is that PRs only run build plus scan, while merges to main trigger the full deployment path."

**[Choose]**
"GitHub Actions with self-hosted runners since we're in TD's network and need access to Nexus and internal registries. I'll use GitHub Environments with protection rules for the staging approval gate."

**[Risk]**
"Three things: secrets isolation — Veracode keys and kubeconfig should be scoped to specific environments. Artifact passing — the Docker image tag needs to flow from the build job to deploy jobs via outputs. And I'll add a smoke test after dev deployment before promoting to staging."

---

## Q10: 修复有 Bug 的 Pipeline YAML

**[Confirm]**
"So I'm given a GitHub Actions workflow with multiple bugs and I need to identify and fix them all."

**[Break]**
"I'll go through the YAML systematically, top to bottom: first check the trigger configuration, then each job's setup — checkout, dependencies, outputs — and finally the inter-job relationships."

**[Choose]**
"I'll use a checklist approach: does every job have checkout? Are outputs properly declared and referenced? Are job dependencies correct? Are deprecated APIs being used? This systematic approach ensures I don't miss anything."

**[Risk]**
"Common traps in these questions: the deprecated set-output syntax — should use GITHUB_OUTPUT now. Missing job dependencies that cause race conditions. And artifacts not being passed between jobs running on different runners."

---

## Q11: 编写并优化 Dockerfile

**[Confirm]**
"So I need to write a Dockerfile for a Java application and then optimize it for image size and security."

**[Break]**
"I'll start with a working but unoptimized version, then improve along three dimensions: size — using multi-stage build to separate build and runtime; security — non-root user and read-only filesystem; build speed — layer caching by copying pom.xml before source code."

**[Choose]**
"Multi-stage build with maven as the builder stage and eclipse-temurin JRE Alpine as the runtime. Alpine because it's minimal — drops the image from 800MB to about 200MB. JRE not JDK since we don't need the compiler at runtime."

**[Risk]**
"Security is key: I'll run as a non-root user, which is a requirement in most enterprise K8s clusters. I'll also add a HEALTHCHECK instruction so Kubernetes can use it, and set MaxRAMPercentage for JVM to respect container memory limits — without this, Java can OOM the container."

---

## Q12: 排查 Pod 故障

**[Confirm]**
"So I need to analyze why a Pod is in CrashLoopBackOff and write out the systematic troubleshooting commands."

**[Break]**
"I'll follow a top-down approach: first, describe pod to check events and exit codes; second, check logs including previous container's logs; third, verify resources, configmaps, and secrets; fourth, interactive debug if needed."

**[Choose]**
"kubectl describe and logs are always the starting point. The exit code tells me the direction: 137 means OOM, 1 means application crash, 0 means unexpected exit. This narrows down the investigation immediately."

**[Risk]**
"Key thing: always use --previous flag for logs, because the current container might be restarting and have no useful logs yet. Also, I'll check namespace-level events — sometimes the issue is at the node level, like insufficient resources or image pull failures, which won't show in container logs."

---

## Q13: 编写 Kubernetes Manifest + Helm Template

**[Confirm]**
"So I need a complete Deployment, Service, and Ingress for the WebBroker API, templated with Helm to support dev and prod environments."

**[Break]**
"I'll create the Helm chart with three templates: deployment with probes and resource management; service for internal routing; and separate values files for each environment. The key templating points are replica count, resource limits, and image tags."

**[Choose]**
"Helm over Kustomize because the team already uses Helm and we need conditional logic — like optional tolerations and environment-specific annotations. I'll use values files for environment differences rather than template branching."

**[Risk]**
"Important details: I'll add a configmap checksum annotation so pods automatically restart when config changes. RollingUpdate with maxUnavailable=0 for zero-downtime. And I'll make sure resource requests are set — without them, HPA can't calculate utilization."

---

## Q14: 写一个 Ansible Playbook

**[Confirm]**
"So I need an Ansible playbook to configure RHEL servers: install packages, deploy templated config files, start the service, and set up firewall rules."

**[Break]**
"I'll organize tasks in logical order: install dependencies → create app user → deploy config via template → install systemd service → configure firewall → start service → health check verification."

**[Choose]**
"I'll use handlers for service restarts instead of inline restart tasks — this ensures idempotency: if the config didn't change, the service won't restart unnecessarily. I'll also use tags so we can run individual sections like just config deployment."

**[Risk]**
"Two things: the template validate parameter — I'll validate the config file before deploying so a bad config doesn't take the service offline. And the health check at the end with retries — the service needs time to start, so I'll use uri module with retries and delay to confirm it's actually healthy."

---

## Q15: Terraform 资源定义与 State Drift

**[Confirm]**
"So I need to write Terraform for an AKS cluster and explain how to detect and handle state drift."

**[Break]**
"Two parts: first, the AKS resource definition with proper networking, node pool config, and tagging; second, the state management strategy — remote backend, drift detection, and remediation approaches."

**[Choose]**
"Azure RM provider with a remote backend in Azure Storage for state. This gives us state locking and team collaboration. I'll use Azure CNI for networking since WebBroker needs VNet integration, and Calico for network policies."

**[Risk]**
"State drift is the biggest operational risk with Terraform. I'll set up scheduled terraform plan in CI to detect drift proactively. The rule should be: all changes go through code and PR review, never manual portal changes. If drift does happen, we decide case by case: apply to enforce code state, or import to adopt the manual change."

---

## 速记总结

```
每题开口的节奏：

1. CONFIRM  → "So the task is..."         (5秒)
2. BREAK    → "I'll do N steps..."         (10秒)
3. CHOOSE   → "I'll use X because Y..."    (10秒)
4. RISK     → "Things to handle: ..."      (10秒)
5. CODE     → "OK let me start coding..."  (开写)

总共 30-40 秒，然后动手。
```

### 万能加分句（写完代码后）

- "In production, I'd also add **unit tests** for this script"
- "This could be **integrated into our GitHub Actions pipeline** as a PR check"
- "I've done something similar at TD when I **[具体经验]**"
- "If I had more time, I'd add **retry logic / parallel processing / structured logging**"
