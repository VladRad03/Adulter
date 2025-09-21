
from typing import Any
from autogen import ConversableAgent
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import RoundRobinPattern, AutoPattern

from google_calendar_tool import send_event_to_google_calendar, get_calendar_events, delete_event_from_google_calendar
from webhook_tool import send_event_to_webhook
class Interpreter:
    
    def __init__(self, llm_config):
        
        calendar_agent_message = """
            You are a smart scheduling agent that receives natural language about calendar events.
            You first ensure you have all of the necessary information to create a calendar event
            Then you will check if there is any conflicting events with get_calendar_events
            then you will try to use the information to create a scheduling call
            Your job is to parse the text and create a structured calendar JSON object.
            
            The JSON must include:
                summary: str  (title of the event)
                description: Optional[str]
                location: Optional[str]
                start: dict with keys:
                    - dateTime: str (ISO 8601 format, e.g., 2025-09-22T13:00:00-07:00)
                    - timeZone: str (e.g., "America/Los_Angeles")
                end: dict with keys:
                    - dateTime: str (ISO 8601 format)
                    - timeZone: str
            
            Then call the provided `send_event_to_webhook` function with this JSON. 

            output "all tasks complete" when you are finished
        """
        def is_termination_msg(msg: dict[str, Any]) -> bool:
            content = msg.get("content", "")
            return (content is not None) and "all tasks complete" in content

        # The scheduling agent
        self.calendar_bot = ConversableAgent(
            name="calendar_agent",
            llm_config=llm_config,
            system_message=calendar_agent_message,
            functions=[send_event_to_webhook, send_event_to_google_calendar, get_calendar_events, delete_event_from_google_calendar],
        )

        # Human agent (for oversight / interactive debugging)
        self.human = ConversableAgent(
            name="human",
            human_input_mode="ALWAYS",
        )
        
        self.pattern = AutoPattern(
            initial_agent=self.calendar_bot,
            agents=[self.calendar_bot],
            user_agent=self.human,
            group_manager_args={
                "llm_config": llm_config,
                "is_termination_msg": is_termination_msg,
            },
        )

    def interpret(self, user_input: str):
        """Run a single scheduling request through the LLM agents and return the result."""
        task_prompt = f"User request: {user_input}\nCreate a structured calendar event JSON."
        result, _, _ = initiate_group_chat(
            pattern=self.pattern,
            messages=task_prompt,
        )
        return result
