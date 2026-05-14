# 给下一个 AI 的交接说明

你将接手的是 FlowBot 的 OpenSpec + FlowGuard MVP。用户已经从“只整理资料”推进到“开始工作”, 当前已经有最小 Python 运行时、FlowGuard 模型、从 FlowPilot 裁剪出的 native startup intake、烟测脚本和端到端 demo；Cockpit/长期心跳仍不是本轮 MVP。

当前版本: `0.1.0`

本地 Codex skill 已安装:

```text
C:\Users\liu_y\.codex\skills\flowbot
```

请先阅读本文件夹内所有文件:

- `README.md`
- `current_requirements.md`
- `workflow_mermaid.md`
- `letter_system.md`
- `reuse_from_flowpilot.md`
- `openspec_flowguard_runtime_plan.md`
- `docs/runtime_contracts.md`
- `docs/flowguard_adoption_log.md`
- `flowbot/`
- `flowbot_models/`
- `scripts/`
- `openspec/changes/flowbot-model-first-runtime/`

## 当前最重要结论

FlowBot 的核心不是普通 AI 计划器。

FlowBot 的核心是:

```text
OpenSpec 管 FlowBot 自身需求/设计/任务
PM 用 FlowGuard 把用户任务建模成路线
Router 执行从模型拓扑导出的 linear route
Controller 只递信和管理 PM/Worker
Worker 只执行当前节点
PM 审查证据并最终验收
```

## 必须保护的角色边界

Controller 必须存在, 但必须保持 relay-only:

- 建立/连接 PM 和 Worker。
- 递送 Router 授权的信封。
- 收回结果和回执。
- 记录角色状态。
- 不拆路线。
- 不执行任务。
- 不审查证据。
- 不从聊天历史推断下一步。

PM 是 Project Manager:

- 合并 Planner 和 Reviewer。
- 负责用户目标理解。
- 负责 FlowGuard route model。
- 负责从模型 topology 导出 linear route。
- 负责审查 Worker 证据。
- 负责最终完成验收。

Worker:

- 只处理当前 work letter 或 repair letter。
- 不跳步。
- 不改路线。

Router:

- 确定性状态机。
- 只接受完整 route package。
- 只按 linear route 当前节点推进。
- 控制 pass/reject/retry/pause/done。

## OpenSpec 状态

OpenSpec 已初始化。

当前变更:

```text
openspec/changes/flowbot-model-first-runtime/
```

已创建:

- `proposal.md`
- `design.md`
- `specs/startup-intake/spec.md`
- `specs/model-first-route-planning/spec.md`
- `specs/controller-letter-execution/spec.md`
- `tasks.md`

当前 24 个任务已经全部勾选完成。继续开发或归档前, 先跑:

```powershell
openspec validate flowbot-model-first-runtime
```

## FlowGuard 状态

本机当前可 import FlowGuard:

```text
flowguard.SCHEMA_VERSION = 1.0
```

FlowGuard 在 FlowBot 中有两层:

1. 开发期验证 FlowBot 自己的 Router/Controller/信件协议。
2. 运行期由 PM 用来生成每次用户任务的路线模型和 linear route。

## FlowPilot 复用参考

完整 FlowPilot 项目在本机可参考:

```text
C:\Users\liu_y\Documents\FlowGuardProjectAutopilot_20260430
```

实际启动 UI 资产:

```text
assets/readme-screenshots/startup-intake.png
docs/ui/startup_intake_desktop_preview/
skills/flowpilot/assets/ui/startup_intake/
```

FlowBot 第一版应复用这个 UI 的简单 bootloader 形态, 不要扩展成复杂 Cockpit。

当前已实现的 FlowBot 裁剪版:

```text
flowbot/assets/ui/startup_intake/flowbot_startup_intake.ps1
assets/brand/flowbot-icon.png
scripts/run_flowbot_from_intake.py
scripts/run_flowbot_startup_intake_smoke.ps1
scripts/check_flowbot_skill_install.py
```

## 当前 demo

打开 native startup intake:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File flowbot\assets\ui\startup_intake\flowbot_startup_intake.ps1
```

运行:

```powershell
python scripts/run_flowbot_demo.py --request "用 FlowBot 把这个复杂请求整理成模型优先路线，并生成一个可验收的最终报告。"
```

成功后检查:

- `.flowbot/runs/<run-id>/router_state.json` 的 `status` 为 `DONE`。
- `.flowbot/runs/<run-id>/pm/route_package.json` 包含 PM 的模型优先路线包。
- `.flowbot/runs/<run-id>/pm/flowguard_result.json` 显示 FlowGuard 检查通过。
- `.flowbot/runs/<run-id>/artifacts/final_report.md` 存在。

## 下一步建议

1. 归档 OpenSpec 变更前, 复跑 FlowGuard、烟测和 OpenSpec validate。
2. 再把 PM/Worker 从 deterministic demo class 替换成真实后台智能体适配层。
3. 最后扩展长路线任务、返工路径、暂停/需要用户输入和 demo 可视化。
