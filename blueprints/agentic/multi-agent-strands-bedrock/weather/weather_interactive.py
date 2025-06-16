from weather_assistant import weather_assistant

def interactive_agent():
    print("\n📁 Weather Agent\n")
    print("Ask a question about the weather forecast or alerts.\n\n")

    print("You can try following queries:")
    print("- What's the weather in Orlando, Florida?")
    print("- Any weather alerts for Las Vegas today?")
    print("Type 'exit' to quit.")

    # Interactive loop
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break

            # response = interactive_agent(
            #     user_input,
            # )
            response = weather_assistant(user_input)

            # Extract and print only the relevant content from the specialized agent's response
            content = str(response)
            print(content)

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try asking a different question.")
