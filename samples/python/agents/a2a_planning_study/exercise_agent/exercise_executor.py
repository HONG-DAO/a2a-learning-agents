# ruff: noqa: E501
# pylint: disable=logging-fstring-interpolation
import logging
from typing import Any, override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_agent_text_message, new_task, new_text_artifact
# Import agent mới có chức năng tạo bài tập
from agents.a2a_planning_study.exercise_agent.exercise_agent import ExerciseGeneratorAgent

logger = logging.getLogger(__name__)

class ExerciseGeneratorAgentExecutor(AgentExecutor):
    """ExerciseGeneratorAgentExecutor sử dụng agent để tạo bài tập và xuất ra mã nguồn."""

    def __init__(self, mcp_tools: list[Any]):
        """Khởi tạo ExerciseGeneratorAgentExecutor với danh sách công cụ MCP."""
        super().__init__()
        logger.info(
            f'Initializing ExerciseGeneratorAgentExecutor with {len(mcp_tools) if mcp_tools else "no"} MCP tools.'
        )
        self.agent = ExerciseGeneratorAgent(mcp_tools=mcp_tools)

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task

        if not context.message:
            raise Exception('No message provided')

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        full_code = ""  # Lưu trữ toàn bộ nội dung bài tập

        # Gọi agent tạo bài tập với luồng streaming
        async for event in self.agent.stream(query, task.contextId):
            if event['is_task_complete']:
                full_code += event['content']
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        append=False,
                        contextId=task.contextId,
                        taskId=task.id,
                        lastChunk=True,
                        artifact=new_text_artifact(
                            name='generate_assignment',
                            description='Generated assignment and result',
                            text=full_code,
                        ),
                    )
                )
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(state=TaskState.completed),
                        final=True,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
            elif event['require_user_input']:
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.input_required,
                            message=new_agent_text_message(
                                event['content'],
                                task.contextId,
                                task.id,
                            ),
                        ),
                        final=True,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
            else:
                # Tiếp tục ghi nhận phần mã tiếp theo
                full_code += event['content']
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.working,
                            message=new_agent_text_message(
                                event['content'],
                                task.contextId,
                                task.id,
                            ),
                        ),
                        final=False,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )

    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
