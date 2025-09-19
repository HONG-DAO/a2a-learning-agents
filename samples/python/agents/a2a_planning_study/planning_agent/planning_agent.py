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


class StudyPlannerAgent:
    SYSTEM_INSTRUCTION = """You are a study planning assistant. Your job is to help users plan their study schedules, recommend study resources, and break down complex topics into manageable learning goals. Be specific, actionable, and encouraging in your recommendations."""

    RESPONSE_FORMAT_INSTRUCTION: str = (
        'Select status as "completed" if the request is fully addressed and no further input is needed. '
        'Select status as "input_required" if you need more information from the user or are asking a clarifying question. '
        'Select status as "error" if an error occurred or the request cannot be fulfilled.'
    )

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self, mcp_tools: list[Any]):
        logger.info('Initializing StudyPlannerAgent with preloaded MCP tools...')
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
            raise ValueError('No MCP tools provided to StudyPlannerAgent')

    async def ainvoke(self, query: str, session_id: str) -> dict[str, Any]:
        logger.info(f"StudyPlannerAgent.ainvoke called with query: '{query}', session_id: '{session_id}'")
        try:
            planner_agent = create_react_agent(
                self.model,
                tools=self.mcp_tools,
                checkpointer=memory,
                prompt=self.SYSTEM_INSTRUCTION,
                response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
            )
            config: RunnableConfig = {'configurable': {'thread_id': session_id}}
            langgraph_input = {'messages': [('user', query)]}
            await planner_agent.ainvoke(langgraph_input, config)
            return self._get_agent_response_from_state(config, planner_agent)
        except httpx.HTTPStatusError as http_err:
            return {
                'is_task_complete': True,
                'require_user_input': False,
                'content': f'HTTP error: {http_err.response.status_code}'
            }
        except Exception as e:
            return {
                'is_task_complete': True,
                'require_user_input': False,
                'content': f'Unexpected error: {str(e)}'
            }

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
            'content': 'We are unable to process your request at the moment. Please try again.'
        }

    async def stream(self, query: str, session_id: str) -> AsyncIterable[Any]:
        agent_runnable = create_react_agent(
            self.model,
            tools=self.mcp_tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
        )
        config: RunnableConfig = {'configurable': {'thread_id': session_id}}
        langgraph_input = {'messages': [('user', query)]}

        try:
            async for chunk in agent_runnable.astream_events(langgraph_input, config, version='v1'):
                event = chunk.get('event')
                data = chunk.get('data', {})
                content = None

                if event == 'on_tool_start':
                    content = f"Using tool: {data.get('name', 'unknown')}"
                elif event == 'on_chat_model_stream':
                    message_chunk = data.get('chunk')
                    if isinstance(message_chunk, AIMessageChunk) and message_chunk.content:
                        content = message_chunk.content

                if content:
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': content
                    }

            final_response = self._get_agent_response_from_state(config, agent_runnable)
            yield final_response

        except Exception as e:
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': f'Error during streaming: {str(e)}'
            }
