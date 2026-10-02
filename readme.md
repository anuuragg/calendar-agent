# Calendar Agent

Calendar Agent is an AI-powered personal calendar assistant that lets users interact with their Google Calendar using natural language.

Instead of manually creating, searching, moving, or deleting calendar events, users can simply describe what they want, and the agent uses tool calling to perform the appropriate calendar operations.

The project uses **Groq** for the LLM and the **Google Calendar API** for real calendar operations. It maintains conversation history, understands dates and times in the user's timezone, and supports event details such as duration and descriptions/notes.

### Current Capabilities

- List Google Calendar events
- Create events with a title, date, time, duration, and description
- Move existing events
- Delete events
- Understand natural-language date and time requests
- Maintain conversational context across multiple messages
- Use Google OAuth for secure Calendar access

### Tech Stack

- **Python**
- **Groq**
- **Google Calendar API**
- **Google OAuth 2.0**
- **Function / Tool Calling**
- **python-dotenv**