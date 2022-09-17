#!/usr/bin/env python
import requests, json, uuid
import os.path
from bs4 import BeautifulSoup
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.errors
from colorama import Fore, Style
import asyncio
import aiohttp


loc = os.path.dirname(os.path.realpath(__file__))
TOKEN_PATH = os.path.join(loc, "token.json")
CREDENTIALS_PATH = os.path.join(loc, "credentials.json")
CAL_PATH = os.path.join(loc, "cal.json")


def date2utc(txt):

    if isinstance(txt, (list, tuple)):
        return [date2utc(x) for x in txt]

    month, day, year, start, end = txt.split(" ")

    startUTC = str(datetime.strptime(" ".join([month, day, year, start]), r"%b %d %Y %I:%M%p")).replace(" ", "T")
    endUTC = str(datetime.strptime(" ".join([month, day, year, end]), r"%b %d %Y %I:%M%p")).replace(" ", "T")

    return startUTC, endUTC


# taken from quickstart.py
def get_service():

    SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except:
                os.remove(TOKEN_PATH)
                return get_service()
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


async def check(url, session):
    session : aiohttp.ClientSession
    async with session.get(url) as response:
        return response.status

async def multiprocessing_func(events):
    url_list = [
        ev.get('description', "https://httpstat.us/400") for ev in events
    ]

    tasks = []
    async with aiohttp.ClientSession() as session:
        for i in url_list:
            tasks.append(asyncio.create_task(check(i, session)))
        return await asyncio.gather(*tasks)

def check_event_status(service):
    """Checks if the event is still active. If not, it deletes it."""

    events = (
        service.events()
        .list(
            calendarId=json.load(open(CAL_PATH))["calendarId"],
            singleEvents=True,
        )
        .execute()
        .get("items", [])
    )
    events = [ev for ev in events if "physics.upenn.edu/events/" in ev.get("description", "")]
    
    if events:
        
        loop = asyncio.get_event_loop()
        statuses = loop.run_until_complete(multiprocessing_func(events))
        to_delete = [(events[i],statuses[i]) for i in range(len(events)) if statuses[i] != 200]

        for ev,stat in to_delete:
            service.events().delete(
                calendarId=json.load(open(CAL_PATH))["calendarId"],
                eventId=ev["id"],
            ).execute()
            print(f"{Fore.RED}Deleted event ({stat}): {ev['summary']}{Style.RESET_ALL}")


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
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, title + starttime + endtime)).replace("-", "a"),
    }
    
    (
    service.events()
    .insert(calendarId=json.load(open(CAL_PATH))["calendarId"], body=event)
    .execute()
    )


def main():

    MAIN_WWW = "https://www.physics.upenn.edu"

    q = requests.get(MAIN_WWW + "/events/").text
    web = BeautifulSoup(q, "html.parser")
    try:
        MAX_PAGES = int(web.find("li", {"class": "pager__item pager__item--last"}).find("a").get("href").split("=")[-1])
    except:
        MAX_PAGES = 0

    events_created = 0
    total_events = 0
    service = get_service()

    check_event_status(service)
    
    for i in range(MAX_PAGES + 1):
        q = requests.get(MAIN_WWW + "/events/?page=%i" % i).text
        web = BeautifulSoup(q, "html.parser")

        info = web.find_all("h3", {"class": "events-title"})
        times = web.find_all("time")
        loc = web.find_all("div", {"class": "metainfo"})
        loc = list(map(lambda x: x.text.split("\n")[-1].strip(), loc))
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

        for event in events:
            try:
                create_event(service, event)
                print(f"{Fore.GREEN}Event created: {event[0]}{Style.RESET_ALL}")
                events_created += 1
            except googleapiclient.errors.HttpError as e:
                if e.status_code == 409:
                    print(f"{Fore.LIGHTBLACK_EX}(409) Duplicate event found ({event[0]}). Skipping...{Style.RESET_ALL}")
                elif e.status_code == 400:
                    print(f"{Fore.LIGHTBLACK_EX}(404) Invalid event found ({event[0]}). Skipping...{Style.RESET_ALL}")
                else:
                    raise e

    print("%i event%s created!" % (events_created, "s" if events_created != 1 else ""))
    print(f"Total events planned: {Fore.GREEN}%i{Style.RESET_ALL}" % (total_events))


if __name__ == "__main__":
    main()
