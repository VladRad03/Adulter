import os
import requests
import json
from utils import get_todays_date
from typing import Annotated, List, Dict
def save_assignments(assignments, filename="assignments.json"):
    """
    Saves assignments to a local JSON file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2)
    print(f"✅ Saved {len(assignments)} assignments to {filename}")
def load_assignments(filename="assignments.json"):
    """
    Loads assignments from a local JSON file.
    Returns an empty list if file does not exist.
    """
    import os
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def canvas_get_all(url, headers, params=None):
    """
    Fetch all pages from a Canvas API endpoint.
    """
    results = []
    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        results.extend(response.json())

        # Parse pagination headers
        links = response.links
        url = links.get("next", {}).get("url")
        params = None  # Only needed on first request
    return results
def get_upcoming_assignments(max_courses: Annotated[int, "Maximum number of courses to check"] = 10)-> List[Dict]:
    """
    Fetches upcoming assignments from Canvas LMS.

    Args:
        max_courses (int): Maximum number of courses to check (default=10).

    Returns:
        List[Dict]: A list of assignments with course name, assignment name, and due date.
    """
    API_URL = os.getenv("CANVAS_API_URL")
    TOKEN = os.getenv("CANVAS_API_TOKEN")
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
    #url = f"{API_URL}/courses"
    #response = requests.get(url, headers=headers)
    #response.raise_for_status()
    #courses = response.json()
    url = f"{API_URL}/courses"
    courses = canvas_get_all(url, headers)

    assignments = []
    for course in courses[:max_courses]:
        course_id = course["id"]
        assignments_url = f"{API_URL}/courses/{course_id}/assignments"
        try:
            print(course["name"])
        except Exception as e:
            print(f"exception thrown: {e}")
        r = requests.get(assignments_url, headers=headers)
        if r.status_code == 200:
            for assignment in r.json():
                if assignment.get("due_at"): # only assignments with due dates
                    assignments.append({
                        "course": course["name"],
                        "name": assignment["name"],
                        "due_at": assignment.get("due_at")
                    })
    return assignments


def filter_future_assignments(assignments: List[Dict]) -> List[Dict]:
    """
    Filters a list of assignments to only include those due after today's date.

    Args:
        assignments (List[Dict]): A list of assignments, each with at least "due_at".

    Returns:
        List[Dict]: A filtered list containing only future assignments.
    """
    today = get_todays_date()
    return [a for a in assignments if a.get("due_at") and a["due_at"] > today]
def get_future_assignments() -> list[dict]:
    """
    Retrieve and filter upcoming assignments to only include those
    due after today's date.

    Returns:
        list[dict]: A list of assignment objects with due dates in the future.
    """
    filtered_assignments = load_assignments(filename="assignments.json")
    print(filtered_assignments)
    if len(filtered_assignments) != 0:
        return filtered_assignments
    assignments = get_upcoming_assignments(-1)
    filtered_assignments = filter_future_assignments(assignments)
    save_assignments(filtered_assignments)
    return filtered_assignments
def test_canvas_api():

    assignments = get_upcoming_assignments(-1)
    print(assignments)
    filtered_assignments = filter_future_assignments(assignments)
    print(filtered_assignments)
    save_assignments(filtered_assignments)

