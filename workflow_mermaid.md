# FlowBot 工作流草图

这是当前 MVP 已实现的主流程。FlowBot 已有从 FlowPilot 裁剪的 native startup intake；headless demo 仍保留用于快速验证。

```mermaid
flowchart TD
    A[用户明确请求使用 FlowBot] --> B[打开 FlowBot startup intake UI]
    B --> C{用户是否确认}
    C -- 取消 --> X[结束: 不创建 run 不启动后台]
    C -- 确认 --> D[UI 写 intake body/result/receipt/envelope]
    D --> E[Router 创建 .flowbot run]
    E --> F[Controller 建立 PM 和 Worker]
    F --> G[Router 发 route_model_request 给 PM]
    G --> H[PM 提取 user contract 和 route hypothesis]
    H --> I[PM 建立 FlowGuard route model]
    I --> J{模型是否暴露路线缺口}
    J -- 有缺口 --> K[PM 修正模型 topology]
    K --> I
    J -- 可抽路线 --> L[PM 从 topology 导出 linear route]
    L --> M[Router 接受 route package]
    M --> N{是否还有未完成节点}
    N -- 没有 --> Z[PM 最终验收并完成]
    N -- 有 --> O[Router 为当前节点生成 work letter]
    O --> P[Controller 递给 Worker]
    P --> Q[Worker 执行当前节点并提交 checkin]
    Q --> R[Router 请求 PM 审查证据]
    R --> S{PM 审查结果}
    S -- pass --> T[Router 标记节点通过并更新 Mermaid]
    T --> N
    S -- reject --> U{是否超过重试上限}
    U -- 否 --> V[Router 生成当前节点 repair letter]
    V --> P
    U -- 是 --> W[暂停并报告用户]
    S -- needs_user --> W
```

建议状态:

```text
INTAKE_WAITING
INTAKE_CANCELLED
RUN_CREATED
ROLES_READY
PM_MODELING
ROUTE_PACKAGE_SUBMITTED
ROUTE_ACCEPTED
NODE_DISPATCHED
WORKER_SUBMITTED
PM_REVIEWING
NODE_PASSED
NODE_REJECTED
NODE_RETRYING
PAUSED
DONE
```

关键原则:

- Controller 只递信和管理后台智能体。
- PM 用 FlowGuard 生成路线, 不是先写普通计划再验证。
- Router 只执行 PM 从模型拓扑中导出的 linear route。
- Worker 每轮只处理当前节点。
- 审查失败只退回当前节点。
- 用户始终通过 Mermaid 看到大进度。
