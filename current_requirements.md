# FlowBot 当前需求整理

## 用户原始意图

用户希望新建一个独立项目 FlowBot。FlowBot 从 FlowPilot 中抽出最有价值的低层流程能力, 但保持轻量。

FlowBot 的定位:

- 不像 FlowGuard 那么底层。
- 不像 FlowPilot 那么高层和重型。
- 不做普通 AI 计划器。
- 使用 OpenSpec 管 FlowBot 自身需求/设计/任务。
- 使用 FlowGuard 作为 PM 在运行时生成路线的建模媒介。
- 使用 Router + Controller + PM + Worker + 信件系统来管理长任务执行。

## 预期入口

用户只有明确要求“用 FlowBot”时才启动 FlowBot。

用户打开 FlowBot 后:

1. 弹出类似 FlowPilot startup intake 的轻量输入窗口。
2. 用户输入工作要求。
3. 用户选择是否启用后台智能体。
4. 用户点击确定。
5. UI 写入 intake body/result/receipt/envelope。
6. Router 创建 `.flowbot/runs/<run-id>/`。
7. Controller 建立或连接 PM 和 Worker。

MVP 不需要:

- Cockpit UI
- heartbeat
- scheduled continuation
- 六角色团队
- 长期恢复

## 核心角色

### Router

- 负责确定性状态机。
- 负责判断当前合法下一步。
- 负责接受或拒绝 PM route package。
- 负责按 linear route 当前节点生成 work letter。
- 负责 pass/reject/retry/pause/done 状态推进。
- 负责更新 Mermaid 进度。
- 不拆路线。
- 不执行任务。
- 不审查 Worker 结果。

### Controller

- 负责建立或连接后台智能体 PM 和 Worker。
- 负责把 Router 授权的信封递给对应智能体。
- 负责收回 PM/Worker 的结果信封和回执。
- 负责记录投递、回执和角色存活状态。
- 不读取 sealed body, 除非明确契约允许。
- 不拆路线。
- 不执行任务。
- 不审查证据。
- 不根据聊天历史推断下一步。

### PM

PM 是 Project Manager, 合并 Planner 和 Reviewer。

PM 第一阶段负责路线生成:

- 读取用户目标。
- 提取 user contract。
- 形成 route hypothesis。
- 建立 FlowGuard route model。
- 根据模型发现修正 topology。
- 从 topology 抽出 one-direction linear route。
- 生成 node acceptance contracts。
- 生成 Mermaid 进度图初稿。

PM 后续阶段负责验收:

- 审查 Worker checkin。
- 必须查看真实证据, 不能只相信 Worker 自述。
- 返回 pass / reject / needs_user。
- reject 时只给当前节点返工要求。
- 最终做完成验收。

### Worker

- 主执行者。
- 每次只接收当前 work letter 或 repair letter。
- 不自行跳步。
- 不自行重写路线。
- 完成后提交 worker_checkin 和证据。

## FlowGuard 在 FlowBot 中的位置

FlowGuard 有两层用途:

1. 开发期: 验证 FlowBot 自己的 Router/Controller/信件状态机。
2. 运行期: PM 用 FlowGuard 把用户任务从模糊想法建模成可执行路线。

运行期 FlowGuard 不是“PM 写好计划后的验证器”。正确顺序是:

```text
用户目标
-> PM 提取 user contract
-> PM 形成 route hypothesis
-> PM 建 FlowGuard route model
-> PM 根据模型发现修正 topology
-> PM 从 topology 抽出 linear route
-> Router 按 linear route 执行
```

## 成功标准

一个最小 FlowBot 应该能做到:

1. 接收用户任务。
2. 通过 startup intake 生成 intake 文件。
3. 创建 run 目录。
4. Controller 建立 PM 和 Worker。
5. PM 用 FlowGuard 生成路线模型和线性路线。
6. Router 接受完整 route package。
7. Router 派发当前 work letter 给 Worker。
8. Worker 提交 checkin 和证据。
9. PM 审查证据。
10. Router 根据 PM 结果推进、返工、暂停或完成。
11. Mermaid 持续显示进度。

## 非目标

MVP 阶段不做:

- 完整 FlowPilot 自动驾驶。
- 多 officer 或六角色团队。
- 长期心跳系统。
- 复杂项目管理平台。
- Cockpit UI。
- 让 Controller 成为会计划/会执行的 AI。
- 一开始生成所有未来提示词。
- 让 Worker 看完整路线自由发挥。

## 复用要求

优先复用 FlowPilot 已有资产:

- startup intake UI 的形态和部分代码。
- Router 状态推进思想。
- Controller relay 和 envelope/receipt 思想。
- packet/card/mailbox 格式经验。
- Mermaid 进度图生成方式。
- `.flowpilot/runs/` 的目录经验, 简化为 `.flowbot/runs/`。

复用边界:

- 复用轻量机制, 不搬完整 FlowPilot。
- 删除 FlowBot 不需要的 heartbeat、Cockpit、多 officer 和长期恢复。
- 保留 Router/Controller/PM/Worker 的清晰责任边界。
