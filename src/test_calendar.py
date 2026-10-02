from google_calendar import get_calendar_service


service = get_calendar_service()

print("Successfully authenticated with Google Calendar!")

calendar = service.calendars().get(
    calendarId="primary"
).execute()

print("Calendar:", calendar["summary"])