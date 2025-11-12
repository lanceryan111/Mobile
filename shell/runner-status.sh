#!/bin/bash
RUNNER_DIR="/Users/runner/actions-runner"
cd "$RUNNER_DIR"

# 检查进程是否存活
if ! pgrep -f "Runner.Listener" >/dev/null; then
  echo "$(date) - Runner not running, restarting..." >> runner_health.log
  ./svc.sh start
else
  echo "$(date) - Runner OK" >> runner_health.log
fi

#!/bin/bash
RUNNER_DIR="/Users/runner/actions-runner"
cd "$RUNNER_DIR"

LOG_FILE="$RUNNER_DIR/runner_health.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 检查 Runner.Listener 是否在运行
if ! pgrep -f "Runner.Listener" >/dev/null; then
  echo "$DATE - Runner not running, attempting restart..." >> "$LOG_FILE"
  ./svc.sh start >> "$LOG_FILE" 2>&1
else
  echo "$DATE - Runner OK" >> "$LOG_FILE"
fi

很好 👍 那我们来一步一步完成一个 macOS self-hosted runner 自动健康检查 + 自启动配置。

⸻

🧰 一、目标

我们要做到：
	1.	runner 宕掉或 crash 时自动检测
	2.	自动重启
	3.	重启后系统会自动恢复运行（开机自启）

⸻

🧩 二、准备目录与脚本

假设 runner 安装在：

/Users/runner/actions-runner

1️⃣ 创建一个健康检查脚本：

sudo nano /Users/runner/actions-runner/check-runner.sh

内容如下：

#!/bin/bash
RUNNER_DIR="/Users/runner/actions-runner"
cd "$RUNNER_DIR"

LOG_FILE="$RUNNER_DIR/runner_health.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 检查 Runner.Listener 是否在运行
if ! pgrep -f "Runner.Listener" >/dev/null; then
  echo "$DATE - Runner not running, attempting restart..." >> "$LOG_FILE"
  ./svc.sh start >> "$LOG_FILE" 2>&1
else
  echo "$DATE - Runner OK" >> "$LOG_FILE"
fi

保存后：

chmod +x /Users/runner/actions-runner/check-runner.sh


⸻

🧭 三、创建 LaunchAgent 定时任务

2️⃣ 创建 plist 文件：

sudo nano ~/Library/LaunchAgents/com.github.runner.check.plist

内容如下（⚠️ 请确认 UserName 和路径）：

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.github.runner.check</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/runner/actions-runner/check-runner.sh</string>
    </array>

    <key>StartInterval</key>
    <integer>300</integer>
    <!-- 每 300 秒（5 分钟）执行一次 -->

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/runner/actions-runner/check-runner.out</string>

    <key>StandardErrorPath</key>
    <string>/Users/runner/actions-runner/check-runner.err</string>
</dict>
</plist>

保存退出。

⸻

🧩 四、加载并验证

加载任务：

launchctl load ~/Library/LaunchAgents/com.github.runner.check.plist

查看是否成功：

launchctl list | grep com.github.runner.check

立即执行一次（测试用）：

launchctl start com.github.runner.check

然后查看日志：

cat /Users/runner/actions-runner/runner_health.log


⸻

🧱 五、效果说明

✅ 每 5 分钟自动检测 runner 状态
✅ 若 Runner.Listener 未运行，会执行 svc.sh start 重启
✅ 在系统重启后，LaunchAgent 会自动随用户登录加载

⸻

是否要我帮你改成 LaunchDaemon（系统级开机自启，无需用户登录） 版本？适用于 server 类 macOS（比如 runner 是后台机）。