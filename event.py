import requests
import os.path
from bs4 import BeautifulSoup
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.errors
import json, uuid
from astropy.time import Time
from colorama import Fore, Style


def date2utc(txt):

    if isinstance(txt, (list, tuple)):
        return [date2utc(x) for x in txt]

    month, day, year, start, end = txt.split(" ")

    startUTC = str(datetime.strptime(" ".join([month, day, year, start]), r"%b %d %Y %I:%M%p")).replace(" ", "T")
    endUTC = str(datetime.strptime(" ".join([month, day, year, end]), r"%b %d %Y %I:%M%p")).replace(" ", "T")

    return startUTC, endUTC


# taken from quickstart.py
def get_service():

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def create_event(service, deets):
    title, location, starttime, endtime, link = deets

    event = {
        "summary": title,
        "description": link,
        "location": location,
        "start": {
            "dateTime": starttime,
            "timeZone": "America/New_York",
        },
        "end": {
            "dateTime": endtime,
            "timeZone": "America/New_York",
        },
        "reminders": {
            "useDefault": True,
        },
        # this creates a unique id for each event so as to make sure we don't get duplicate events
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, title + starttime + endtime)).replace("-", ""),
    }
    event = service.events().insert(calendarId=json.load(open("cal.json"))["calendarId"], body=event).execute()


def main():

    MAIN_WWW = "https://www.physics.upenn.edu"

    q = requests.get(MAIN_WWW + "/events/").text

    web = BeautifulSoup(q, "html.parser")
    MAX_PAGES = int(web.find("li", {"class": "pager__item pager__item--last"}).find("a").get("href").split("=")[-1])

    events_created = 0
    total_events = 0
    for i in range(MAX_PAGES + 1):
        print("On page", i + 1)
        q = requests.get(MAIN_WWW + "/events/?page=%i" % i).text
        web = BeautifulSoup(q, "html.parser")

        info = web.find_all("h3", {"class": "events-title"})
        times = web.find_all("time")
        loc = web.find_all("div", {"class": "metainfo"})
        loc = list(map(lambda x: x.text.split("\n")[-1].lstrip(" ").rstrip(" "), loc))
        loc = [l if l else "N/A - Check link" for l in loc]

        titles = [t.find("a").text for t in info]
        links = [MAIN_WWW + t.find("a").get("href") for t in info]

        # grab all time elements
        elements = [times[n::5] for n in range(5)]
        # convert em all to strings
        elements = list(map(lambda x: [a.text for a in x], elements))
        # transpose
        elements = list(zip(*elements))
        # concat each element to a single string per events
        event_str = list(map(lambda x: " ".join(x), elements))
        # convert to start and end times in utc
        event_str = list(map(date2utc, event_str))
        starttimes, endtimes = list(zip(*event_str))
        # transpose to get a list of each element per event
        events = list(zip(*[titles, loc, starttimes, endtimes, links]))
        total_events += len(events)

        service = get_service()
        for event in events:
            try:
                create_event(service, event)
                print(f"{Fore.GREEN}Event created: {event[0]}{Style.RESET_ALL}")
                events_created += 1
            except googleapiclient.errors.HttpError as e:
                if e.status_code == 409:
                    print(f"{Fore.LIGHTBLACK_EX}Duplicate event found. Skipping...{Style.RESET_ALL}")
                else:
                    raise e

    print("%i event%s created!" % (events_created, "s" if events_created != 1 else ""))
    print(f"Total events: {Fore.GREEN}%i{Style.RESET_ALL}" % len(total_events))


if __name__ == "__main__":
    main()
