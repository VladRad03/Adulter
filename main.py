import os
from interpreter import Interpreter

# Fake minimal LLM config (adapt to your provider: OpenAI, Claude, local, etc.)
llm_config = {
    "model": "gpt-4",  # or "gpt-3.5-turbo"
    "api_key": os.getenv("OPENAI_API_KEY", "dummy_key"),  # fallback for demo
}

# Get API_URL from environment

def main():
    print("=== Calendar Scheduling Agent ===")
    print("Type 'quit' to exit.\n")

    # Initialize Interpreter
    agent = Interpreter(llm_config=llm_config)

    while True:
        user_input = input("Describe your event: ")

        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break
        elif user_input.lower() in ["example"]:
            user_input = "soccer game september 24th 2025, from 4pm-6pm at UW IMA in Seattle, use google calendar."

        # Run agent
        result = agent.interpret(user_input)

        # Print agent’s result
        print("\n--- Result ---")
        print(result)
        print("--------------\n")


if __name__ == "__main__":
    main()
