# -*- coding: utf-8 -*-
"""DeepSeek 与 OpenAI 兼容文本模型客户端。"""

import json
from collections.abc import AsyncGenerator, Sequence
from typing import Any
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.messages.utils import message_chunk_to_message
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI

from app.core import settings
from app.utils.error import Error


class DeepSeekClient:
    """DeepSeek客户端"""

    def __init__(self):
        """
        初始化DeepSeek客户端
        :return:
        """
        if not settings.DEEPSEEK_APIKEY:
            raise Error(code=500, message="未配置DEEPSEEK_APIKEY")

        self.model = settings.deepseek_model
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_APIKEY,
            base_url=settings.deepseek_base_url,
        )
        chat_model_kwargs: dict[str, Any] = {}
        if "deepseek" in settings.deepseek_base_url.lower():
            chat_model_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        self.chat_model = ChatOpenAI(
            api_key=settings.DEEPSEEK_APIKEY,
            base_url=settings.deepseek_base_url,
            model=self.model,
            **chat_model_kwargs,
        )

    async def json_completion(
            self,
            system_prompt: str,
            user_prompt: str,
            max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        获取json格式的大模型输出
        :param system_prompt: 系统提示词
        :param user_prompt: 用户提示词
        :param max_tokens: 最大输出长度
        :return:
        """
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]
        last_decode_error: json.JSONDecodeError | None = None
        for attempt in range(2):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={
                        "type": "json_object",
                    },
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                if not content:
                    raise Error(code=502, message="DeepSeek返回内容为空")
                return json.loads(content)
            except json.JSONDecodeError as e:
                last_decode_error = e
                if attempt == 0:
                    messages.append({
                        "role": "user",
                        "content": (
                            "上一次输出不是合法JSON，无法解析。"
                            f"解析错误：{e}。请重新完整输出一个合法JSON对象，"
                            "不要输出Markdown、解释文字或未转义换行。"
                        ),
                    })
                    continue
                raise Error(code=502, message=f"DeepSeek返回JSON解析失败：{last_decode_error}") from e
            except Error:
                raise
            except Exception as e:
                raise Error(code=502, message=f"DeepSeek调用失败：{e}") from e
        if last_decode_error is not None:
            raise Error(code=502, message=f"DeepSeek返回JSON解析失败：{last_decode_error}") from last_decode_error
        raise Error(code=502, message="DeepSeek JSON调用失败")

    async def text_completion(
            self,
            system_prompt: str,
            user_prompt: str,
            max_tokens: int = 2048,
    ) -> str:
        """
        获取文本格式的大模型输出
        :param system_prompt: 系统提示词
        :param user_prompt: 用户提示词
        :param max_tokens: 最大输出长度
        :return: 文本内容
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if not content:
                raise Error(code=502, message="DeepSeek返回内容为空")
            return content
        except Error:
            raise
        except Exception as e:
            raise Error(code=502, message=f"DeepSeek调用失败：{e}") from e

    async def agent_completion_stream(
            self,
            messages: list[BaseMessage | dict[str, Any]],
            tools: Sequence[BaseTool | dict[str, Any]] | None = None,
            max_tokens: int = 4096,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        使用LangChain模型绑定工具并流式获取Agent输出
        :param messages: 对话消息
        :param tools: 可供模型自主选择的工具
        :param max_tokens: 最大输出长度
        :return:
        """
        try:
            model = self.chat_model
            if tools:
                openai_tools = [
                    self._normalize_openai_tool(tool)
                    for tool in tools
                ]
                model = model.bind(tools=openai_tools, tool_choice="auto")
            model = model.bind(max_tokens=max_tokens)
            content_chunks = []
            gathered: AIMessageChunk | None = None
            async for chunk in model.astream(messages):
                gathered = chunk if gathered is None else gathered + chunk
                content = chunk.content
                if content:
                    text = self._content_to_text(content)
                    content_chunks.append(text)
                    yield {
                        "event": "delta",
                        "content": text,
                    }
            assistant_message = (
                message_chunk_to_message(gathered)
                if gathered is not None
                else AIMessage(content="")
            )
            yield {
                "event": "complete",
                "content": "".join(content_chunks),
                "assistant_message": assistant_message,
            }
        except Error:
            raise
        except Exception as e:
            raise Error(code=502, message=f"DeepSeek调用失败：{e}") from e

    @staticmethod
    def _content_to_text(content: str | list[Any]) -> str:
        """
        将LangChain消息内容规整为前端可流式展示的文本
        :param content: LangChain消息内容
        :return:
        """
        if isinstance(content, str):
            return content
        return "".join(
            item.get("text", "")
            if isinstance(item, dict) and item.get("type") == "text"
            else str(item)
            for item in content
        )

    @staticmethod
    def _normalize_openai_tool(tool: BaseTool | dict[str, Any]) -> dict[str, Any]:
        """
        将LangChain工具规整为OpenAI-compatible tools数组元素
        :param tool: LangChain工具或已经转换过的工具dict
        :return:
        """
        openai_tool = convert_to_openai_tool(tool) if isinstance(tool, BaseTool) else dict(tool)
        function_schema = openai_tool.get("function")
        if not isinstance(function_schema, dict):
            return openai_tool
        parameters = function_schema.get("parameters")
        if isinstance(parameters, dict):
            parameters.setdefault("type", "object")
            parameters.setdefault("title", f"{function_schema.get('name', 'tool')}_args")
        return openai_tool
