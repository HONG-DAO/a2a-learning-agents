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

from agents.a2a_planning_study.planning_agent.planning_agent import StudyPlannerAgent

logger = logging.getLogger(__name__)

class StudyPlannerAgentExecutor(AgentExecutor):
    """StudyPlannerAgentExecutor sử dụng agent lập kế hoạch học tập với các công cụ MCP."""

    def __init__(self, mcp_tools: list[Any]):
        """Khởi tạo StudyPlannerAgentExecutor với danh sách công cụ MCP đã nạp sẵn."""
        super().__init__()
        logger.info(
            f'Initializing StudyPlannerAgentExecutor with {len(mcp_tools) if mcp_tools else "no"} MCP tools.'
        )
        self.agent = StudyPlannerAgent(mcp_tools=mcp_tools)

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

        # Gọi agent lập kế hoạch học tập với luồng streaming
        async for event in self.agent.stream(query, task.contextId):
            if event['is_task_complete']:
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        append=False,
                        contextId=task.contextId,
                        taskId=task.id,
                        lastChunk=True,
                        artifact=new_text_artifact(
                            name='study_plan',
                            description='Generated study plan or result.',
                            text=event['content'],
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
