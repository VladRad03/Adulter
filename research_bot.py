from openai import OpenAI
from typing import Optional
def research_online(query: str) -> Optional[str]:
  """
    Performs an online research task using GPT-5 with web search preview.
    
    This function acts as a research assistant for an agent. It:
    - Accepts a vague goal or research query.
    - Uses GPT-5 with web search to gather relevant, factual, and actionable information.
    - Summarizes the findings in clear text for downstream agents to process.
    
    Parameters:
    -----------
    query : str
        A user-provided goal or topic to research.
    
    Returns:
    --------
    str or None
        A concise summary of the research findings. Returns None if the call fails.
    """
  try:
    client = OpenAI()
    #query = "find papers combining differential privacy and Machine Learning"
    response = client.responses.create(
        model="gpt-5",
        input=[
            {
                "role": "system",
                "content": [
                    {"type": "input_text", "text": "You are a Research Assistant AI. Your task is to gather relevant, factual, and actionable information about a user-provided goal. You act as the information collector and summarizer for another AI that will generate questions and create a schedule based on your output."}
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": query}
                ],
            },
        ],
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {
                    "type": "approximate",
                    "country": "US",
                    "region": "WA",
                    "city": "Seattle"
                },
                "search_context_size": "low"
            }
        ],
        store=False
    )
    return response.output_text
  except Exception as e:
      print(f"Error during research_online: {str(e)}")
      return None
