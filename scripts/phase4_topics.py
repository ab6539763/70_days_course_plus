"""Shared per-day facts + content generators for the Phase 4 "Agent" days
(Day 39-44). These six days were originally authored by copy-pasting the
Day 37 (Self-RAG citation/rewrite) template and only patching the six
"override" files (01/03/04/10/11/17/18/24) plus the embedded code snippets.
The remaining ~19 narrative files per day kept Day 37's prose verbatim
(citations, rewrite, cross-encoder, 口语命中 ...), which is nonsensical for
an Agent/orchestration day. This module rebuilds those files with content
that actually matches each day's topic.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Phase4Day:
    day: int
    req: str
    ver: str
    topic: str
    subtitle: str
    modules: tuple[tuple[str, str], ...]
    api_config: str
    api_preview: str
    api_extra: tuple[str, ...]
    chat_flag: str
    trace_field: str
    trace_extra: tuple[str, ...]
    demo_files: tuple[str, ...]
    review_file: str
    tests_dir: str
    tests_count: int
    core_class: str
    prev_day: int
    prev_topic: str
    prev_sentence: str
    next_day: int
    next_topic: str
    key_sentence: str
    story_problem: str
    story_solution: str
    case_studies: tuple[tuple[str, str, str], ...] = field(default_factory=tuple)
    quiz: tuple[tuple[str, str], ...] = field(default_factory=tuple)


DAYS: dict[int, Phase4Day] = {
    39: Phase4Day(
        day=39, req="ZL-NA-REQ-039", ver="v0.39.0",
        topic="手写 ReAct Agent",
        subtitle="Thought → Action → Observation 可观测工具链",
        modules=(
            ("agent/react_agent.py", "ReActAgent — Thought/Action/Observation 循环"),
            ("agent/react_config.py", "ReactConfig — max_steps / use_session_history"),
        ),
        api_config="/api/agent/react-config", api_preview="/api/agent/react-preview",
        api_extra=(), chat_flag="agent_mode", trace_field="agent_trace",
        trace_extra=("tools_used",),
        demo_files=("day39/react_demo.py", "day39/react_api_demo.py"),
        review_file="day39/phase4_react_review.py",
        tests_dir="tests/day39/", tests_count=17, core_class="ReActAgent",
        prev_day=38, prev_topic="多轮 Self-RAG 校验重试",
        prev_sentence="Day38 让校验失败后能重试；",
        next_day=40, next_topic="AgentExecutor 框架工具链",
        key_sentence="Day38 让校验能重试；Day39 让 Agent 能自己选工具。",
        story_problem="客服机器人遇到「查电话」「查收益」混合问句时只能走固定分支，新增场景要改分支代码，运营等不起。",
        story_solution="引入 ReAct 循环：模型先 Thought（判断该用哪个工具），再 Action 调用 ToolExecutor，观察 Observation 后决定继续或给出 Final Answer。",
        case_studies=(
            ("多轮追问", "用户先问「客服电话」再问「收益率」", "同一 session 内两次独立 Thought→Action，agent_trace 分别记录"),
            ("工具不存在", "Thought 选中一个未注册工具名", "ToolExecutor 抛错，Observation 返回错误文本，Agent 仍能给出兜底回复"),
            ("步数超限", "max_steps=3 但问题需要 4 步", "第 3 步后强制生成 Final Answer，避免死循环"),
        ),
        quiz=(
            ("ReAct 三阶段分别是？", "Thought / Action / Observation"),
            ("Day39 的 agent_trace 里每一步含哪些字段？", "step/thought/action/action_input/observation/final_answer"),
        ),
    ),
    40: Phase4Day(
        day=40, req="ZL-NA-REQ-040", ver="v0.40.0",
        topic="AgentExecutor 框架工具链",
        subtitle="StructuredTool + invoke + intermediate_steps",
        modules=(
            ("agent/structured_tool.py", "StructuredTool + @tool 装饰器 + OpenAI schema"),
            ("agent/tool_adapter.py", "ToolRegistry → StructuredTool 适配"),
            ("agent/agent_executor.py", "AgentExecutor.invoke 可观测循环"),
            ("agent/executor_config.py", "ExecutorConfig — max_iterations"),
        ),
        api_config="/api/agent/executor-config", api_preview="/api/agent/executor-preview",
        api_extra=(), chat_flag="executor_mode", trace_field="executor_trace",
        trace_extra=("tools_used",),
        demo_files=("day40/executor_demo.py", "day40/executor_api_demo.py"),
        review_file="day40/phase4_executor_review.py",
        tests_dir="tests/day40/", tests_count=17, core_class="AgentExecutor",
        prev_day=39, prev_topic="手写 ReAct Agent",
        prev_sentence="Day39 手写 ReAct 循环验证了思路；",
        next_day=41, next_topic="StateGraph 状态图编排",
        key_sentence="Day39 手写 ReAct 验证思路；Day40 用 StructuredTool 把工具注册框架化。",
        story_problem="Day39 的 ReAct 循环里，每个工具的入参 schema 是手写字典，新增工具要改多处代码，容易漏字段。",
        story_solution="引入 LangChain 风格 @tool 装饰器 + StructuredTool：从函数签名自动推导 OpenAI function-calling schema，AgentExecutor.invoke 统一调度并记录 intermediate_steps。",
        case_studies=(
            ("新增工具零改动", "运营要求新增「工单查询」工具", "写一个带类型标注的函数 + @tool 装饰器即可注册，无需改 AgentExecutor 代码"),
            ("schema 校验前置", "工具入参类型不对", "StructuredTool.to_openai_tool() 导出的 schema 可直接喂给真实模型做 function-calling 校验"),
            ("与 ReAct 对比", "同一问题分别跑 Day39/Day40", "intermediate_steps 与 agent_trace 结构一致，便于灰度切换"),
        ),
        quiz=(
            ("StructuredTool 由什么生成 schema？", "函数签名 + 类型标注"),
            ("AgentExecutor 与 ReActAgent 的核心差异？", "工具注册方式框架化，其余循环逻辑一致"),
        ),
    ),
    41: Phase4Day(
        day=41, req="ZL-NA-REQ-041", ver="v0.41.0",
        topic="StateGraph 状态图编排",
        subtitle="planner → tool_runner → answer 显式节点图",
        modules=(
            ("agent/state_graph.py", "StateGraph — add_node/add_edge/compile/invoke"),
            ("agent/graph_state.py", "AgentGraphState 节点间共享状态"),
            ("agent/rag_agent_graph.py", "RAGAgentGraph 三节点预置图"),
            ("agent/graph_config.py", "GraphConfig — max_iterations"),
        ),
        api_config="/api/agent/graph-config", api_preview="/api/agent/graph-preview",
        api_extra=(), chat_flag="graph_mode", trace_field="graph_trace",
        trace_extra=("node_path", "tools_used"),
        demo_files=("day41/graph_demo.py", "day41/graph_api_demo.py"),
        review_file="day41/phase4_graph_review.py",
        tests_dir="tests/day41/", tests_count=17, core_class="RAGAgentGraph",
        prev_day=40, prev_topic="AgentExecutor 框架工具链",
        prev_sentence="Day40 AgentExecutor 用一个线性 while 循环调度工具；",
        next_day=42, next_topic="人工审批工作流",
        key_sentence="Day40 AgentExecutor 是线性 invoke；Day41 用 StateGraph 显式声明节点与边，为后续加审批节点铺路。",
        story_problem="产品要求「先规划、再执行工具、最后单独一步生成答案」三个阶段要能分别插桩、分别测试，AgentExecutor 的单一 while 循环耦合太紧。",
        story_solution="引入轻量 StateGraph：add_node 注册 planner/tool_runner/answer 三个节点，add_conditional_edges 控制何时回到 planner、何时进入 answer，node_path 记录实际走过的节点序列。",
        case_studies=(
            ("插桩审计", "合规要求记录每一步决策节点", "node_path 直接给出 planner→tool_runner→answer 的完整轨迹"),
            ("提前收敛", "简单问题不需要工具", "planner 判定后条件边直接跳到 answer，跳过 tool_runner"),
            ("为审批铺路", "Day42 需要在工具执行后插入人工审批", "只需在 tool_runner 和 answer 之间插入新节点，无需重写整个循环"),
        ),
        quiz=(
            ("StateGraph 的三个核心 API？", "add_node / add_edge(或 add_conditional_edges) / invoke"),
            ("node_path 记录什么？", "本次调用实际经过的节点名称序列"),
        ),
    ),
    42: Phase4Day(
        day=42, req="ZL-NA-REQ-042", ver="v0.42.0",
        topic="人工审批工作流",
        subtitle="human_approval 节点 + checkpoint 中断恢复",
        modules=(
            ("agent/approval_config.py", "ApprovalConfig — require_rag_approval / mock_auto_approve"),
            ("agent/approval_checkpoint.py", "中断检查点存取"),
            ("agent/approval_workflow_graph.py", "human_approval 节点 + resume"),
        ),
        api_config="/api/agent/approval-config", api_preview="/api/agent/approval-preview",
        api_extra=("/api/agent/approval-resume",), chat_flag="approval_mode",
        trace_field="approval", trace_extra=("graph_trace",),
        demo_files=("day42/approval_demo.py", "day42/approval_api_demo.py"),
        review_file="day42/phase4_approval_review.py",
        tests_dir="tests/day42/", tests_count=16, core_class="ApprovalWorkflowGraph",
        prev_day=41, prev_topic="StateGraph 状态图编排",
        prev_sentence="Day41 StateGraph 能编排任意节点图；",
        next_day=43, next_topic="Supervisor 多 Agent 委派",
        key_sentence="Day41 让节点图可编排；Day42 在图里加入人工审批卡点，管住高风险 RAG 输出。",
        story_problem="合规要求：涉及具体收益率数字的回答，必须有人工复核后才能发给客户，但当前 chat 接口是全自动直出。",
        story_solution="在 StateGraph 的 tool_runner 之后插入 human_approval 节点：命中 require_rag_approval 规则时中断执行并返回 checkpoint_id，人工调用 approval-resume 携带 approved/comment 后流程续跑。",
        case_studies=(
            ("高风险问句拦截", "用户问「年化收益率能到多少」", "human_approval 中断，chat 响应 interrupted=true + checkpoint_id"),
            ("人工通过", "审核员调用 approval-resume approved=true", "流程从中断点续跑，返回最终 reply"),
            ("人工驳回", "审核员 approved=false + comment", "流程终止并返回拒答说明，不发原始 RAG 结果"),
        ),
        quiz=(
            ("中断后靠什么恢复执行？", "checkpoint_id + approval-resume"),
            ("chat 响应里 approval 字段何时非空？", "approval_mode=true 且触发了审批逻辑时"),
        ),
    ),
    43: Phase4Day(
        day=43, req="ZL-NA-REQ-043", ver="v0.43.0",
        topic="Supervisor 多 Agent 委派",
        subtitle="faq_worker / rag_worker / intent_worker",
        modules=(
            ("agent/supervisor_config.py", "SupervisorConfig — max_delegations"),
            ("agent/sub_agent.py", "三个专职子 Agent"),
            ("agent/supervisor_graph.py", "supervisor_route → worker → synthesize"),
        ),
        api_config="/api/agent/supervisor-config", api_preview="/api/agent/supervisor-preview",
        api_extra=(), chat_flag="supervisor_mode", trace_field="supervisor_trace",
        trace_extra=("delegated_agents", "tools_used"),
        demo_files=("day43/supervisor_demo.py", "day43/supervisor_api_demo.py"),
        review_file="day43/phase4_supervisor_review.py",
        tests_dir="tests/day43/", tests_count=17, core_class="SupervisorGraph",
        prev_day=42, prev_topic="人工审批工作流",
        prev_sentence="Day42 让单个 Agent 的高风险输出可管控；",
        next_day=44, next_topic="MCP 协议与工具生态",
        key_sentence="Day42 让单 Agent 可管控；Day43 让多个专职 Agent 协作委派。",
        story_problem="随着工具越来越多，一个 Agent 要同时懂 FAQ、RAG 检索、意图分类，Prompt 越写越长，维护成本飙升。",
        story_solution="引入 Supervisor 模式：supervisor_route 节点先判断问题类型，再委派给 faq_worker / rag_worker / intent_worker 三个专职子 Agent 之一执行，最后 synthesize 节点汇总成统一回复。",
        case_studies=(
            ("客服电话查询", "「客服电话多少」", "委派 faq_worker → faq_lookup 工具"),
            ("产品收益咨询", "「年化收益怎么样」", "委派 rag_worker → rag_search 工具"),
            ("模糊归纳请求", "「帮我总结一下理财产品」", "委派 intent_worker → intent_classify 工具"),
        ),
        quiz=(
            ("Supervisor 有哪三个子 Agent？", "faq_worker / rag_worker / intent_worker"),
            ("delegated_agents 字段记录什么？", "本次委派经过的子 Agent 名称列表"),
        ),
    ),
    44: Phase4Day(
        day=44, req="ZL-NA-REQ-044", ver="v0.44.0",
        topic="MCP 协议与工具生态",
        subtitle="自研 MCP Server — tools/list + tools/call",
        modules=(
            ("agent/mcp_config.py", "McpConfig — server_name / mock_routing / max_tool_calls"),
            ("agent/mcp_protocol.py", "JSON-RPC tools/list + tools/call 消息类型"),
            ("agent/mcp_server.py", "NexusMcpServer — 暴露 ToolRegistry"),
            ("agent/mcp_client.py", "McpClient — list/call 封装"),
            ("agent/mcp_bridge.py", "MCP → StructuredTool 桥接"),
            ("agent/mcp_runner.py", "discover → route → call → answer"),
        ),
        api_config="/api/agent/mcp-config", api_preview="/api/agent/mcp-preview",
        api_extra=("/api/agent/mcp-list-tools",), chat_flag="mcp_mode",
        trace_field="mcp_trace", trace_extra=("mcp_tools", "tools_used"),
        demo_files=("day44/mcp_demo.py", "day44/mcp_api_demo.py"),
        review_file="day44/phase4_mcp_review.py",
        tests_dir="tests/day44/", tests_count=20, core_class="McpRunner",
        prev_day=43, prev_topic="Supervisor 多 Agent 委派",
        prev_sentence="Day43 Supervisor 让多个内嵌子 Agent 能协作；",
        next_day=45, next_topic="Dify 工作流对接与周测",
        key_sentence="Day43 让 Agent 可协作；Day44 让工具链可扩展 — 用 MCP 协议对接进程外/未来的外部工具。",
        story_problem="SubAgent 的三个工具都是进程内直调，若要接入第三方团队独立维护的工具（甚至跨语言），Supervisor 现有委派方式无法复用；需要一套与厂商无关的协议边界。",
        story_solution="自研一个符合 MCP（Model Context Protocol）语义的 Server：对外暴露 tools/list（发现工具 schema）与 tools/call（按名调用），McpRunner 按 discover→route→call→answer 四阶段驱动，未来把进程内 Server 换成真实外部 MCP 服务时业务代码无需改动。",
        case_studies=(
            ("客服电话查询", "「客服电话多少」", "tools/list 发现 faq_lookup → tools/call 执行 → mcp_trace 记录四阶段"),
            ("产品收益咨询", "「年化收益怎么样」", "路由到 rag_search，走同一套 MCP 调用管线"),
            ("未来切换真实 MCP Server", "把 NexusMcpServer 换成外部进程/HTTP MCP 端点", "McpClient/McpRunner 接口不变，只替换 transport 层"),
        ),
        quiz=(
            ("MCP 的两个核心方法是？", "tools/list 与 tools/call"),
            ("mcp_trace 里 phase 字段有哪几种取值？", "discover / route / call / answer"),
        ),
    ),
}


def get(day: int) -> Phase4Day:
    return DAYS[day]
