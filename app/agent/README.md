# app.agent 目录说明

`app.agent` 负责模型客户端、具体智能体和 LangGraph 工作流编排。这里不追求额外抽象层：每个功能尽量像 `path.py`、`profile.py` 一样，一眼能看到这个类做什么、入口是什么、结果给谁用。

## 目录结构

```text
app/agent
├─ client.py            # DeepSeek / OpenAI-compatible 文本模型客户端
├─ profile.py           # 七维学生画像智能体
├─ path.py              # 个性化学习路径规划智能体
├─ quiz_review.py       # 测验完成后的复盘点评与画像更新智能体
├─ vision.py            # 图片预解析模型客户端
├─ knowledge            # PDF/基础库检索、Qdrant 操作和两个检索工具类
├─ notebook             # 中央对话、Studio 产物工具和内容质检
└─ workflow             # LangGraph 状态图、工具注册、工具执行、Studio 质检回环
```

## 当前工具

知识库工具在 `knowledge/tools.py`：

- `UserKnowledgeSearchTool`：查当前笔记本用户 PDF。
- `BaseKnowledgeSearchTool`：查系统基础知识库。

Studio 产物工具在 `notebook/tools.py`：

- `LearningPathStudioTool`
- `StudyGuideStudioTool`
- `BriefingStudioTool`
- `MindmapStudioTool`
- `FlashcardStudioTool`
- `QuizStudioTool`
- `DataTableStudioTool`
- `CodePracticeStudioTool`

`StudioAgent` 只是一个门面：根据 `artifact_type` 选择对应 Studio 工具并调用 `run(...)`。真正的生成逻辑在具体工具类里。

测验复盘入口在 `quiz_review.py`：

- `QuizReviewAgent`：只在完整提交测验后运行，根据得分、错题和当前画像输出复盘点评、画像更新原因和新的七维画像。
- 它不是 Studio 生成工具，也不进入中央对话 LangGraph 回环；API 入口由 `NotebookService.submit_quiz_attempt(...)` 负责校验测验、释放数据库事务、调用智能体并保存画像。

## workflow 做什么

`workflow` 只负责编排，不写具体工具业务：

- 中央对话图：画像分析 -> DeepSeek 自主判断 -> 工具执行 -> ToolMessage 回传 -> DeepSeek 再判断。
- 知识检索工具：执行后直接把检索结果回传给 DeepSeek。
- Studio 工具：DeepSeek 选择后进入 Studio 子图，生成内容，再由内容质检智能体检查；检查完成后返回中央对话。
- service 层拿到已质检的 Studio 结果后入库。

AI 自主调用 Studio 与手动点击 Studio 共用生成链路，但入参边界不同：

- 手动 Studio API 继续使用 `StudioArtifactGenerate`，测验和闪卡数量保持 `fewer`、`standard`、`more` 三档，兼容前端单选控件。
- AI 工具 schema 使用 `StudioToolArgs`，数量参数允许模型直接传明确整数。`workflow/studio_tools.py` 会把整数归一化到三档，同时把明确数量写入 `custom_prompt`，由具体 Studio 工具解析。
- 测验和闪卡的实际条目数在 `notebook/tools.py` 中决定，不依赖模型在 prompt 里自行遵守数量要求；大批量结构化产物按批次生成、清洗、去重后再合并。
- `client.py` 的 JSON 调用对非法 JSON 有一次严格重试；具体 Studio 工具仍要尽量缩小单次 JSON 输出规模，不把大量条目压进一次模型输出。
- Studio 工具执行失败必须通过 ToolMessage 和协作轨迹暴露错误原因，`tool_executor` 会直接结束本轮工作流，中央对话不能绕过 Studio 在聊天正文里假装已生成同等规模产物。

## 新增工具规则

1. 新工具优先写成一个具体类，不新增抽象基类。
2. 工具对外入口保持 `run(...)`，如果要给 API 主动调用，可以再保留清楚的业务方法，例如 `search(...)`。
3. 多个同类小工具可以放在同一个 `tools.py`，不要为了每个轻量工具单独建文件。
4. workflow 只注册和执行工具，不承载具体生成、检索、落库逻辑。
5. 替换旧工具时同步删除旧闭包、旧工厂或旧路由，避免只做加法。
