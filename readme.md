# Calendar Agent

A personal AI calendar assistant that lets you manage your Google Calendar using natural language.

Built with:

- **Groq** for the AI agent
- **Google Calendar API** for calendar data
- **MCP** (Model Context Protocol) for tool communication
- **Streamlit** for the chat interface

## Features

- View calendar events
- Create events
- Move events
- Delete events
- Set event duration
- Add event descriptions
- Understand natural-language dates and times ("tomorrow at 5 PM", "next Friday")

## Example prompts

- What's on my calendar today?
- Schedule a walk at 9 PM for 2 hours
- Schedule a 2 hour brainstorming session tomorrow
- Find my meetings this week
- Move my 3 PM meeting to 5 PM

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/anuuragg/calendar-agent.git
cd calendar-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows, activate it with `venv\Scripts\activate` instead.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Get your Groq API key from [console.groq.com](https://console.groq.com/).

## Google Calendar Setup

The app uses Google OAuth to access your Google Calendar.

### 1. Create Google OAuth credentials

1. In Google Cloud Console, enable the **Google Calendar API**.
2. Create OAuth credentials for a **Desktop App** and download the credentials file.
3. Place it here:

```text
src/credentials.json
```

### 2. Authenticate

Run:

```bash
python src/test_calendar.py
```

A browser window will open. Sign in with your Google account and allow calendar access.

After a successful login, a `token.json` file is created.

> **Keep `credentials.json` and `token.json` private.** Do not commit them. Make sure both are listed in `.gitignore`.

## Run the Application

Once setup is complete, start the Streamlit app:

```bash
streamlit run streamlit_app.py
```

## Architecture

```text
Streamlit UI
     ↓
AI Agent
     ↓
MCP Client
     ↓
MCP Server
     ↓
Google Calendar API
```

- The Streamlit app is the user-facing chat interface.
- The agent sends your message to the model and runs the tools the model asks for.
- The MCP server exposes the calendar tools to the agent.

### MCP tools

| Tool | Purpose |
|---|---|
| `list_events` | List events, optionally by date range or search text |
| `add_event` | Create an event with a title, date, time, duration and optional description |
| `move_event` | Move an event to a new date and time |
| `remove_event` | Delete an event |

## Configuration

- **Model:** set in `src/agent.py` (`MODEL`), served through Groq.
- **Timezone:** set in `src/agent.py` (`TIMEZONE`).

## Project Structure

```text
calendar-agent/
├── mcp/
│   ├── client.py
│   └── server.py
│
├── src/
│   ├── agent.py
│   ├── auth.py
│   ├── chat.py
│   ├── credentials.json
│   ├── google_calendar.py
│   ├── test_calendar.py
│   └── tools.py
│
├── test/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── streamlit_app.py
```