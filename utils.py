def get_goals(file_path: str = "goals.txt") -> list[str]:
    """
    Reads goals line by line from a text file and returns them as a list of strings.
    
    Args:
        file_path (str): Path to the text file containing goals.
        
    Returns:
        list[str]: A list of goals, one per line (ignores empty lines).
    """
    goals = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                goal = line.strip()
                if goal:  # skip empty lines
                    goals.append(goal)
    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
    return goals
from datetime import datetime

def get_todays_date() -> str:
    """
    Returns today's date in ISO 8601 format (YYYY-MM-DD).
    Useful for scheduling tools and setting default time ranges.
    """
    return datetime.now().strftime("%Y-%m-%d")
