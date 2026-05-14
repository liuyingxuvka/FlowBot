# FlowBot

日期: 2026-05-14

状态: 已完成 OpenSpec 变更、最小 Python 运行时、FlowGuard 模型、FlowPilot 裁剪版 native startup intake、烟测脚本和可跑通的端到端 demo。Cockpit、heartbeat、scheduled continuation 和长期恢复不属于本轮 MVP。

版本: `0.1.0`

本地 Codex skill: 已安装到 `C:\Users\liu_y\.codex\skills\flowbot`。

FlowBot 是一个位于 FlowGuard 和 FlowPilot 之间的轻量级 AI 工作循环系统。

- OpenSpec: 负责 FlowBot 自身的需求、设计、规格和任务拆解。
- FlowGuard: 进入 FlowBot 运行时, 由 PM 用作路线生成和建模工具。
- FlowBot: 负责把用户任务转成可执行的一条线性路线, 再由 Router/Controller/PM/Worker 按信件节拍推进。
- FlowPilot: 更高层、更重型, 有多角色、心跳、长期恢复和完整自动驾驶。

## 当前核心判断

FlowBot 的特色不是“AI 会列计划”。它的特色是:

```text
PM 用 FlowGuard 把模糊任务建成模型
-> 从模型拓扑抽出一条单向路线
-> Router 按路线逐节点推进
-> Controller 只负责建立后台智能体和递信
-> Worker 只执行当前信
-> PM 审查证据并决定通过/返工/暂停
```

FlowGuard 不只是开发 FlowBot 时的测试工具, 也不是 PM 写完计划后的盖章工具。它是 PM 从模糊想法走向精细路线的中间建模媒介。

## MVP 角色

FlowBot MVP 只保留两个后台智能体:

- PM: Project Manager, 负责用户目标理解、FlowGuard 建模、路线抽取、节点验收和最终验收。
- Worker: 执行者, 每次只接收当前一封 work letter。

另外保留两个非后台智能体组件:

- Router: 确定性状态机, 控制合法节拍。
- Controller: relay-only 递信器, 负责建立/连接 PM 和 Worker, 递信封, 收回执, 不能计划、执行或审查。

## 入口

FlowBot 启动 UI 第一版应复用/裁剪 FlowPilot startup intake:

- 一个大输入框: 用户输入工作要求。
- 一个开关: 是否启用后台智能体。
- 一个确认按钮。

当前已落地的 native startup intake:

```text
flowbot/assets/ui/startup_intake/flowbot_startup_intake.ps1
```

不保留 FlowPilot MVP 外功能:

- Cockpit UI
- scheduled continuation
- heartbeat
- 六角色团队
- 长期恢复

## 运行主线

```text
用户明确请求使用 FlowBot
-> 打开 FlowBot intake UI
-> UI 写 intake body/result/receipt/envelope
-> Router 创建 run
-> Controller 建立 PM 和 Worker
-> Router 让 Controller 把路线建模请求递给 PM
-> PM 用 FlowGuard 建立并修正 route model
-> PM 从模型拓扑导出 linear route
-> Router 接受 route package
-> Router 当前节点生成 work letter
-> Controller 递给 Worker
-> Worker 执行并提交 checkin
-> PM 审查真实证据
-> Router pass 进入下一节点, reject 只返工当前节点
-> 完成或暂停
```

## OpenSpec

当前 OpenSpec 变更:

```text
openspec/changes/flowbot-model-first-runtime/
```

这个变更定义了三个能力:

- `startup-intake`
- `model-first-route-planning`
- `controller-letter-execution`

该变更的 24 个任务已经完成, 仍保留为后续归档和扩展的需求依据。

## Demo

可以直接打开 FlowBot native startup intake:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File flowbot\assets\ui\startup_intake\flowbot_startup_intake.ps1
```

也可以跑 headless demo:

```powershell
python scripts/run_flowbot_demo.py --request "用 FlowBot 把这个复杂请求整理成模型优先路线，并生成一个可验收的最终报告。"
```

关键验证命令:

```powershell
python scripts/run_flowbot_protocol_checks.py
python scripts/run_flowbot_route_synthesis_checks.py
python scripts/run_flowbot_smoke_checks.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_flowbot_startup_intake_smoke.ps1
python scripts/check_flowbot_skill_install.py
openspec validate flowbot-model-first-runtime
```

demo 成功后会在 `.flowbot/runs/<run-id>/` 下生成:

- `router_state.json`: 最终状态应为 `DONE`。
- `pm/flowguard_result.json`: PM 路线合成模型检查结果。
- `pm/linear_route.json`: 从 FlowGuard 拓扑导出的单向路线。
- `letters/`, `checkins/`, `reviews/`: 每轮信件、Worker 证据和 PM 审查。
- `artifacts/final_report.md`: 最终产物。
