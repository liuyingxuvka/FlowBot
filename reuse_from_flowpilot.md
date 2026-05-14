# FlowPilot 复用清单

用户明确希望 FlowBot 不要全部从零开始。FlowBot 是一个中间层产品, 可以从 FlowPilot 里裁剪已有能力, 形成更轻的单任务循环系统。

当前设计已经明确: FlowBot 保留 FlowPilot 的 Controller/Router/packet 控制思想, 但只使用 PM 和 Worker 两个后台智能体。

## 可以优先复用的东西

### 启动弹窗

FlowBot 一开始可以复用或裁剪 FlowPilot 的 startup intake UI。

候选路径:

```text
C:\Users\liu_y\Documents\FlowGuardProjectAutopilot_20260430\assets\readme-screenshots\startup-intake.png
C:\Users\liu_y\Documents\FlowGuardProjectAutopilot_20260430\docs\ui\startup_intake_desktop_preview\
C:\Users\liu_y\Documents\FlowGuardProjectAutopilot_20260430\skills\flowpilot\assets\ui\startup_intake\
```

FlowBot 需要的版本应该更简单:

- 输入用户需求。
- 点击确定。
- 创建 FlowBot run。
- 只保留是否启用后台智能体的开关。
- 不要求打开复杂 UI。
- 不要求启动完整 FlowPilot 驾驶舱。
- 不要求 scheduled continuation 或 heartbeat。

### 图标和品牌资产

初期可以复用 FlowPilot 图标, 避免为了 MVP 先做品牌资产。

候选路径:

```text
assets/brand/flowpilot-icon-default.png
assets/brand/README.md
```

后续如果 FlowBot 独立成产品, 再替换成自己的 bot 图标。

### Router

FlowBot 可以复用 FlowPilot Router 的思想和部分状态推进逻辑, 但要大幅简化。

候选路径:

```text
skills/flowpilot/assets/flowpilot_router.py
tests/test_flowpilot_router_runtime.py
simulations/flowpilot_router_loop_model.py
simulations/run_flowpilot_router_loop_checks.py
```

FlowBot Router 应保留:

- 接受 PM route package。
- 从 PM 的 linear route 中选择当前节点。
- 当前节点 work letter 派发。
- Worker 打卡接收。
- PM 审查接收。
- pass/reject 状态推进。
- retry 上限。
- pause/done 状态。
- Mermaid 更新。

FlowBot Router 应去掉:

- 多 officer。
- 多层 route tree。
- 长期 daemon/heartbeat。
- 复杂恢复策略。
- FlowPilot 高级自动驾驶语义。

### Controller relay

FlowBot 必须保留 FlowPilot 的 Controller relay 思想, 但大幅简化。

候选参考:

```text
skills/flowpilot/assets/flowpilot_router.py
skills/flowpilot/assets/packet_runtime.py
.flowpilot/runs/*/packet_ledger.json
.flowpilot/runs/*/mailbox/
```

FlowBot Controller 应保留:

- 建立或连接 PM 和 Worker。
- 递送 Router 授权的信封。
- 收回 PM/Worker 结果和回执。
- 记录投递 ledger。
- 报告角色不可用或断开。

FlowBot Controller 应禁止:

- 自己拆路线。
- 自己执行用户任务。
- 自己审查 Worker 结果。
- 读取 sealed body 或用聊天历史当证据。
- 绕过 Router 直接驱动 PM 或 Worker。

### 信件、packet、card 系统

FlowBot 的工作信可以借鉴 FlowPilot 的 packet/card/mailbox 设计。

候选路径:

```text
scripts/flowpilot_packets.py
skills/flowpilot/assets/packet_runtime.py
skills/flowpilot/assets/card_runtime.py
templates/flowpilot/packets/
skills/flowpilot/assets/runtime_kit/cards/
.flowpilot/runs/*/mailbox/
```

FlowBot 至少需要这些轻量信件:

- route_model_request
- route_package
- work_letter
- worker_checkin
- pm_review
- repair_letter

不要把 FlowPilot 全部 card/officer 系统搬进来。

### FlowGuard route modeling

FlowBot 应该把 FlowGuard 放进运行期 PM 规划阶段。

候选参考:

```text
simulations/
skills/flowpilot/assets/runtime_kit/cards/
docs/flowguard_adoption_log.md
```

FlowBot 的 PM 应使用 FlowGuard:

- 提取 user contract。
- 形成 route hypothesis。
- 建 FlowGuard route model。
- 根据模型发现修正 topology。
- 从 topology 抽出 linear route。
- 给每个节点生成 acceptance contract。

不要把 FlowGuard 只当成开发期测试, 也不要只当成计划完成后的验证章。

### Mermaid 进度图

FlowBot 应该保留用户可见的 Mermaid 进度图, 这是用户理解当前执行状态的重要窗口。

候选路径:

```text
scripts/flowpilot_user_flow_diagram.py
templates/flowpilot/diagrams/
.flowpilot/diagrams/
tests/test_flowpilot_user_flow_diagram.py
```

FlowBot 的 Mermaid 图应该展示:

- 总任务。
- PM 建模阶段。
- 当前节点。
- 已通过节点。
- 当前返工节点。
- 暂停原因。
- 最终完成状态。

### 运行目录结构

FlowBot 可以参考 `.flowpilot/runs/`, 但目录更轻。

建议:

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
      mermaid.mmd
      letters/
      checkins/
      reviews/
```

## 总原则

复用 FlowPilot 的已验证机制, 但不要继承 FlowPilot 的复杂度。

FlowBot 的价值是:

```text
FlowPilot 的 Controller/Router/packet 控制思想
+ PM 运行期 FlowGuard 路线建模
- FlowPilot 的重型多角色自动驾驶
= 轻量通用 AI 工作循环器
```
