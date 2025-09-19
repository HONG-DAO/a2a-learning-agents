# ruff: noqa: E501
# pylint: disable=logging-fstring-interpolation
import logging
import os

from collections.abc import AsyncIterable
from typing import Any, Literal

import httpx

from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.runnables.config import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

memory = MemorySaver()


class ResponseFormat(BaseModel):
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


class ExerciseGeneratorAgent:
    SYSTEM_INSTRUCTION = """Bạn là một trợ lý tạo bài tập lập trình thông minh. Hãy tạo ra các bài tập lập trình có chất lượng, đầy đủ, và kèm theo lời giải chi tiết.

Yêu cầu:
- Tạo bài tập lập trình theo yêu cầu người dùng.
- Chỉ tạo bài tập phù hợp với ngôn ngữ lập trình được nêu.
- Mỗi bài tập nên gồm: mô tả bài, yêu cầu đầu vào/đầu ra, ví dụ, và đoạn code lời giải.
- Toàn bộ kết quả phải ở định dạng code hoàn chỉnh, có thể copy vào file và chạy được ngay.
"""

    RESPONSE_FORMAT_INSTRUCTION: str = (
        'Chọn status là "completed" nếu đã hoàn thành bài tập đầy đủ để ghi vào file code. '
        'Chọn status là "input_required" nếu cần thêm thông tin từ người dùng. '
        'Chọn status là "error" nếu gặp lỗi.'
    )

    SUPPORTED_CONTENT_TYPES = ['text/plain', 'text']

    def __init__(self, mcp_tools: list[Any]):
        logger.info('Initializing ExerciseGeneratorAgent with preloaded MCP tools...')
        try:
            model = os.getenv('GOOGLE_GENAI_MODEL')
            if not model:
                raise ValueError('GOOGLE_GENAI_MODEL environment variable is not set')

            if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
                self.model = ChatVertexAI(model=model)
                logger.info('ChatVertexAI model initialized successfully.')
            else:
                self.model = ChatGoogleGenerativeAI(model=model)
                logger.info('ChatGoogleGenerativeAI model initialized successfully.')
        except Exception as e:
            logger.error(f'Failed to initialize model: {e}', exc_info=True)
            raise

        self.mcp_tools = mcp_tools
        if not self.mcp_tools:
            raise ValueError('No MCP tools provided to ExerciseGeneratorAgent')

    def _get_agent_response_from_state(self, config: RunnableConfig, agent_runnable) -> dict[str, Any]:
        state = agent_runnable.get_state(config)
        values = getattr(state, 'values', {})
        structured = values.get('structured_response') if isinstance(values, dict) else None

        if structured and isinstance(structured, ResponseFormat):
            return {
                'is_task_complete': structured.status == 'completed',
                'require_user_input': structured.status == 'input_required',
                'content': structured.message
            }

        messages = values.get('messages', [])
        if messages and isinstance(messages[-1], AIMessage):
            content = messages[-1].content
            if isinstance(content, str):
                return {'is_task_complete': True, 'require_user_input': False, 'content': content}
        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'Không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại.'
        }

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        agent_runnable = create_react_agent(
            self.model,
            tools=self.mcp_tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
        )
        config: RunnableConfig = {'configurable': {'thread_id': session_id}}
        langgraph_input = {'messages': [('user', query)]}

        collected_code = ""

        try:
            async for chunk in agent_runnable.astream_events(langgraph_input, config, version='v1'):
                event = chunk.get('event')
                data = chunk.get('data', {})
                content = None

                if event == 'on_tool_start':
                    content = f"# Đang sử dụng công cụ: {data.get('name', 'unknown')}"
                elif event == 'on_chat_model_stream':
                    message_chunk = data.get('chunk')
                    if isinstance(message_chunk, AIMessageChunk) and message_chunk.content:
                        content = message_chunk.content

                if content:
                    collected_code += content
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': content
                    }

            final_response = self._get_agent_response_from_state(config, agent_runnable)

            if final_response.get("is_task_complete"):
                final_response["collected_code"] = collected_code

            yield final_response

        except Exception as e:
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': f'Lỗi trong quá trình streaming: {str(e)}'
            }
