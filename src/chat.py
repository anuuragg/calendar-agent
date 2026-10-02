from agent import run_agent


def main():
    print("Calendar Agent")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        response = run_agent(user_input)

        if response:
            print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    main()