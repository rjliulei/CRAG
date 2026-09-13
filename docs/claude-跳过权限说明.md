# Claude Code：跳过权限说明

## 放开全部权限

```bash
claude --dangerously-skip-permissions
```

等价写法：

```bash
claude --permission-mode bypassPermissions
```

只把该模式加入 `Shift+Tab` 循环、不马上开启：

```bash
claude --allow-dangerously-skip-permissions
```

## 项目内配置

本仓库已有：

- 目录：`.claude/`
- 文件：`.claude/settings.json`

内容示例：

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

说明：较新版 Claude Code 可能**忽略项目级**的 `bypassPermissions`。若未生效，仍用启动参数，或写到用户目录：

- Windows：`%USERPROFILE%\.claude\settings.json`
- Linux/macOS：`~/.claude/settings.json`

## 报错：root/sudo 不能用

完整报错：

```text
--dangerously-skip-permissions cannot be used with root/sudo privileges for security reasons
```

含义：在 Linux / macOS / WSL 上，当前是 **root 或 sudo** 时，禁止开启跳过权限模式。原生 Windows 一般无此检查。

### 推荐做法：用普通用户

```bash
whoami
su - 你的用户名
cd /path/to/项目
claude --dangerously-skip-permissions
```

容器内请用非 root 的 `USER` 启动。

### 隔离环境临时绕过

```bash
IS_SANDBOX=1 claude --dangerously-skip-permissions
```

或：

```bash
export IS_SANDBOX=1
claude --dangerously-skip-permissions
```

也可使用：`CLAUDE_CODE_BUBBLEWRAP=1`（同样用于通过 root 检查）。

仅建议在容器 / VM 等隔离环境使用；本机日常开发慎用。

## 风险提醒

- 跳过权限后，多数工具调用不再逐次确认。
- 显式 `ask` / `deny` 规则，以及删根目录、主目录等断路器仍可能生效。
- 勿在生产机、含敏感数据的主机上长期开启。
