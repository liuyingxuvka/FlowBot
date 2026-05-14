# FlowBot: OpenSpec + FlowGuard 组合施工计划

## 分工

OpenSpec 负责 FlowBot 项目自身:

- 为什么要做。
- 要做哪些能力。
- 需求和验收标准。
- 设计决策。
- 实施任务清单。

FlowGuard 负责 FlowBot 运行时的任务路线生成:

- PM 从用户目标建立模型。
- PM 根据模型发现修正路线。
- PM 从模型拓扑抽出 linear route。
- Router 按 linear route 执行。

## 关键原则

不要把 FlowGuard 当成“PM 写完计划后的验证器”。

正确关系是:

```text
用户目标
-> PM 初步理解
-> FlowGuard route model
-> 模型迭代修正
-> route topology
-> linear route spine
-> Router 执行
```

## 第一阶段: 规格化

目标: 让下一个 AI 不再靠聊天历史理解 FlowBot。

产物:

- OpenSpec change: `flowbot-model-first-runtime`
- 更新后的中文需求文档
- 明确角色边界
- 明确 FlowGuard 运行期位置

完成标准:

- `openspec validate flowbot-model-first-runtime` 通过。
- 根目录文档不再把 Reviewer/Planner 当作旧称。
- 文档明确 Controller relay-only。
- 文档明确 route_plan 来源于 FlowGuard topology。

## 第二阶段: 协议定义

目标: 先定义文件和状态, 不急着写完整运行器。

需要定义:

```text
.flowbot/
  runs/
    run-YYYYMMDD-HHMMSS/
      intake/
      router_state.json
      controller_ledger.json
      pm/
        user_contract.md
        route_hypothesis.md
        flowguard_route_model.py
        model_findings.md
        route_topology.json
        linear_route.json
        node_acceptance_contracts.json
      letters/
      checkins/
      reviews/
      mermaid.mmd
```

完成标准:

- 每个文件都有 schema 或字段说明。
- Router 状态能表达 intake、PM modeling、route accepted、node dispatch、review、repair、pause、done。
- Controller ledger 能记录投递和回执。

## 第三阶段: 最小 Router + Controller

目标: 不接真实 AI, 先让状态机跑通。

实现范围:

- Router 创建 run。
- Controller 模拟 PM/Worker ready。
- Router 接受模拟 route package。
- Router 派发当前节点。
- Router 接收模拟 checkin/review。
- Router pass/reject/retry/pause/done。

完成标准:

- 取消后不创建 run。
- Controller 不能绕过 Router。
- 未接受 route package 不能派发 Worker。
- reject 只返工当前节点。
- retry 超限暂停。

## 第四阶段: PM FlowGuard route synthesis

目标: 接入 PM 作为路线生成者。

PM 必须提交:

- user_contract
- route_hypothesis
- flowguard_route_model
- model_findings
- route_topology
- linear_route
- node_acceptance_contracts

完成标准:

- Router 能拒绝缺少 FlowGuard artifacts 的 route package。
- PM 产出的 linear route 是从 topology 导出的。
- Mermaid 能显示用户可理解的大路线。

## 第五阶段: Worker 执行和 PM 审查

目标: 完成最小 FlowBot 闭环。

流程:

```text
Router 生成 current work_letter
-> Controller 递给 Worker
-> Worker 返回 checkin
-> Controller 递回 Router
-> Router 请求 PM review
-> PM pass/reject/needs_user
-> Router 推进/返工/暂停
```

完成标准:

- Worker 每次只看到当前 letter。
- PM 审查必须引用证据。
- Mermaid 每轮更新。
- 最终完成需要 PM final acceptance。

## 第六阶段: 从 FlowPilot 裁剪 UI

目标: 使用真实 FlowBot startup intake。

当前状态: 已实现 `flowbot/assets/ui/startup_intake/flowbot_startup_intake.ps1`, 并通过 `scripts/run_flowbot_startup_intake_smoke.ps1` 验证 confirm/cancel 与 runtime 接入。

复用参考:

```text
C:\Users\liu_y\Documents\FlowGuardProjectAutopilot_20260430\skills\flowpilot\assets\ui\startup_intake\
```

裁剪要求:

- 保留大输入框。
- 保留确认/取消。
- 保留 intake result/receipt/envelope/body 思路。
- 只保留 background agents 开关。
- 去掉 Cockpit、scheduled continuation、heartbeat。

完成标准:

- UI confirm 写出 FlowBot intake artifacts。
- UI cancel 不创建 run。
- Router 能读取 intake result。
