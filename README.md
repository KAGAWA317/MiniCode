# MiniCode

MiniCode 是一个**规划中的 Go 终端 AI 编程助手**：类似 ClaudeCode，在交互式终端会话里接收开发任务，在用户指定的工作区中修改文件并执行命令。

> 当前仓库只包含规划文档和一个保留的 Python 离线原型；**尚无 Go 实现，也没有可运行的 MiniCode 命令**。

## 规划文档

- [spec.md](spec.md) — 产品规格：背景、目标用户、已确认能力、非功能要求、设计骨架、完成条件、待确认项与 Out of Scope。
- [tasks.md](tasks.md) — 实施任务：按顺序拆分的 T01～T08，每项标注影响文件、依赖与参考定位。
- [checklist.md](checklist.md) — 验收清单：命名与文档、待定参数、功能、凭据与边界、端到端验收。

## 保留的 Python 原型

根目录的 `agent.py` 是改名前的离线原型，**仅作历史参考**：纯标准库、无网络、不调用任何模型，用确定性规则代替模型策略。它不是 MiniCode 的实现，也不代表目标能力；Go 版本落地前不要把它当作 MiniCode 使用。

```bash
cd MiniCode
python3 agent.py --self-check
python3 agent.py "calc 6*7 then write out.txt: answer={last} then read out.txt"
```

## Go 版本的运行方式（待实现）

Go 版本实现并通过验收后，预期从仓库根目录启动，例如 `go run .`。该命令**当前不可用**——仓库中还没有 `go.mod` 与 Go 源码，请不要据此判断项目已可运行。

## 凭据

beeapi 的服务地址、认证方式、协议与模型选择尚未确认。真实密钥只通过本地环境或本地配置提供，不进入源码、文档或版本控制；`.gitignore` 已排除 `.env` 与 `.env.*`（保留 `.env.example` 作为占位样例）。
