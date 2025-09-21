
from typing import Any
from autogen import ConversableAgent
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import RoundRobinPattern, AutoPattern

from google_calendar_tool import send_event_to_google_calendar, get_calendar_events, delete_event_from_google_calendar
from webhook_tool import send_event_to_webhook
from utils import get_goals, get_todays_date
from canvas_api import get_future_assignments
from research_bot import research_online

from collections import deque
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

            When all events have been scheduled respond "all tasks complete"
        """
        text_interpreter_message = """ You are a smart scheduling assistant. Your task is to receive raw text data—this can be copied text from emails, documents, screenshots (converted to text), assignments, or messages—and summarize it into clear, concise, and actionable schedulable events.
if the user vaguely mentions goals, beckon the goal_planner agent without any other output. This additionally overrules the later mentioned rules.
otherwise your output must include:

1. **Title / Summary**: A short descriptive title for the event or task.
2. **Date**: The day the event or task occurs. If the exact date isn’t mentioned, infer the most likely date.
3. **Time**: Start time and, if possible, end time or approximate time of day (morning, afternoon, evening). Assume Pacific Standard time zone unless otherwise stated.
4. **Location**: If a location is mentioned, include it. Otherwise, leave blank.
5. **Source / Type**: Indicate the source of the information (email, assignment, notes, etc.) or type of task (meeting, homework, personal, work).
6. **Additional Notes**: Include any relevant context, instructions, or dependencies mentioned in the text.
7. **Priority / Urgency**: If indicated or inferable from context, note whether the event is high, medium, or low priority.

**Rules:**
- Extract all actionable events or tasks from the text; do not invent unrelated events.
- Summarize multiple events as separate bullet points or numbered lists.
- Infer missing details reasonably, but do not make up unnecessary information.
- Focus on clarity and conciseness; output should be human-readable and directly schedulable.
- Avoid any formatting like JSON; plain text with clear structure is preferred.

if the user mentions scheduling goals, without being clear what they are beckon the goal planner
"""
        goal_planner_message = """You are a smart scheduling assistant. 
You will be given raw text containing vague personal or work goals. 
Your job is to convert these goals into a clear, concise list of schedulable events.  

For each goal:
- Summarize it into a short event title, or multiple event titles
- Suggest reasonable days and times of day (morning, afternoon, evening) or a specific time if obvious.  
- Suggest an estimated duration (default 1 hour if unclear).  
- Add location if mentioned.  
- Add any extra notes if relevant.  
- assume pacific standard time unless otherwise implied
Output in plain text, one event per line, formatted like this:
[Event Title] — [Day/Date] — [Time/Time of Day] — [Duration] — [Notes if any]  

If information is missing, make a smart assumption (e.g., "afternoon", "1 hour").  
Keep the descriptions short and ready for conversion into a calendar.  
Do not output JSON or code, just clean human-readable text.

the goal is to create a schedule that will help the user reach the goals.
"""
        schedule_checker_message = """
You are a calendar conflict checker and priority evaluator.

You will be given a list of events with their date, time, and duration.  
Your job is to:
1. Check if any events overlap or are too close together.  
2. Identify potential conflicts (e.g., two events at the same time).  
3. Suggest which event should take priority based on common sense, urgency, and importance.  
   - Deadlines and exams are higher priority than flexible tasks.  
   - Work, school, or appointments are higher priority than leisure.  
   - Fixed-time events (like meetings) take priority over flexible goals.  
4. Provide a concise summary of conflicts and recommendations.  

Output format:
- Clearly state conflicts.  
- Recommend which event(s) to reschedule, and when.  
- Suggest a possible resolution schedule.  

if schedule is ready to execute and clear beckon the calendar_agent
"""
        #self.event_queue = deque()  # stores individual events
        def is_termination_msg(msg: dict[str, Any]) -> bool:
            content = msg.get("content", "")
            return (content is not None) and "all tasks complete" in content
        
        # The scheduling agent
        self.calendar_bot = ConversableAgent(
            name="calendar_agent",
            llm_config=llm_config,
            system_message=calendar_agent_message,
            functions=[send_event_to_google_calendar, delete_event_from_google_calendar],
        )
        self.dataInterpreter = ConversableAgent(
            name="data_interpreter",
            llm_config=llm_config,
            system_message=text_interpreter_message,
            functions=[get_todays_date, get_future_assignments],
        )
        self.goal_planner = ConversableAgent(
            name="goal_planner",
            llm_config=llm_config,
            system_message=goal_planner_message,
            functions=[get_goals, research_online],
        )
        self.schedule_checker = ConversableAgent(
            name="schedule_checker",
            llm_config=llm_config,
            system_message=schedule_checker_message,
            functions=[get_calendar_events],
        )
        
        # Human agent (for oversight / interactive debugging)
        self.human = ConversableAgent(
            name="human",
            human_input_mode="ALWAYS",
        )
        
        self.pattern = AutoPattern(
            initial_agent=self.dataInterpreter,
            agents=[self.calendar_bot, self.dataInterpreter, self.schedule_checker, self.goal_planner],
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
            max_rounds=50
        )
        return result
    # def enqueue_events(self, raw_events_text: str):
    #     """
    #     Convert raw text from goal planner or data interpreter into individual events
    #     and add them to the queue.
    #     """
    #     self.text_pattern = AutoPattern(
    #         initial_agent=self.dataInterpreter,
    #         agents=[self.dataInterpreter],
    #         user_agent=self.human,
    #         group_manager_args={
    #             "llm_config": self.llm_config,
    #             "is_termination_msg": is_termination_msg,
    #         },
    #     )

    #     # Example: split by lines
    #     lines = [line.strip() for line in raw_events_text.splitlines() if line.strip()]
    #     for line in lines:
    #         # You could parse into a dict with fields like summary, date, time, etc.
    #         event = {"text": line}  # start simple
    #         self.event_queue.append(event)
    # def process_next_event(self):
    #     """
    #     Pop one event from the queue, send it to the schedule checker, 
    #     then to the calendar bot if ready.
    #     """
    #     if not self.event_queue:
    #         return "No more events in the queue."

    #     event = self.event_queue.popleft()

    #     # Step 1: Check for conflicts / priorities
    #     conflict_result, _, _ = initiate_group_chat(
    #         pattern=self.pattern,
    #         messages=f"Check schedule for event: {event['text']}"
    #     )

    #     # Step 2: If clear, schedule the event
    #     schedule_result, _, _ = initiate_group_chat(
    #         pattern=self.pattern,
    #         messages=f"Schedule this event: {event['text']}"
    #     )

    #     return {
    #         "event": event,
    #         "conflict_check": conflict_result,
    #         "schedule_result": schedule_result
    #     }
