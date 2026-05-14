# FlowBot 信件系统草案

FlowBot 的信件不是普通聊天消息, 而是 Router 控制下的工作单元。每封信应该短、可执行、可验收, 并通过 Controller 递送。

## 建模请求信

```text
类型: route_model_request
收件人: PM

用户目标:
用户在 startup intake 中提交的工作要求。

任务:
请提取 user contract, 形成 route hypothesis, 建立 FlowGuard route model, 根据模型发现修正 topology, 并从 topology 导出 one-direction linear route。

禁止:
不要直接开始执行。
不要让 Controller 参与路线设计。
不要把普通 AI 计划当作最终路线。

输出要求:
user_contract
route_hypothesis
flowguard_route_model
model_findings
route_topology
linear_route
node_acceptance_contracts
mermaid
```

## 路线包

```text
类型: route_package
提交者: PM

user_contract:
用户目标、限制、完成定义。

flowguard_route_model:
PM 用于生成路线的模型。

model_findings:
模型暴露的问题、修正记录、剩余边界。

route_topology:
模型中的节点和流转。

linear_route:
从 topology 抽出的单向主线, 形如 Node 1 -> Node 2 -> ... -> Done。

node_acceptance_contracts:
每个节点的完成标准和证据要求。
```

## 工作信

```text
类型: work_letter
收件人: Worker
节点编号: 1
标题: 当前节点名称

目标:
本节点要完成什么。

范围:
允许修改或处理的内容。

禁止:
明确不能做什么。

输入材料:
当前节点需要读取的文件、上下文、需求或上一步结果。

完成标准:
什么事实可以证明本节点完成。

输出要求:
Worker 完成后必须返回什么, 比如文件列表、diff 摘要、测试结果、日志、截图或阻塞点。
```

## 打卡信

```text
类型: worker_checkin
提交者: Worker
节点编号: 1
状态: submitted

实际完成:
Worker 声明完成的内容。

产物:
文件、命令输出、日志、截图或其他证据。

未完成/风险:
Worker 发现的问题。

需要审查:
希望 PM 重点看的地方。
```

## 审查信

```text
类型: pm_review
提交者: PM
节点编号: 1
结论: pass | reject | needs_user

依据:
PM 读取到的事实依据。

问题:
如果 reject 或 needs_user, 必须列出阻塞通过的问题。

返工指令:
如果 reject, 只针对当前节点给出短指令。

下一步建议:
如果 pass, 可以提示 Router 进入下一节点。
```

## 修复信

```text
类型: repair_letter
收件人: Worker
节点编号: 1
来源: pm_rejection

当前问题:
审查失败的具体原因。

修复目标:
Worker 这次只需要修复什么。

不能做:
不要扩大范围, 不要重做已经通过的部分。

重新提交要求:
修复后重新打卡, 并附上证据。
```

## 设计原则

- 信件由 Router 授权, 由 Controller 递送。
- Controller 不能根据内容自己改信或推进状态。
- PM 的第一封核心输出是 FlowGuard-backed route package。
- Worker 不接收完整复杂路线, 只接收当前节点信。
- PM 审查必须基于真实证据, 不能只看 Worker 自述。
- 信件历史必须持久化, 方便审计和恢复。
