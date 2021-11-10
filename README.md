# UPennPhysCal
A nasty but easy way to keep your GCal updated with department colloquia. Depends on `bs4`, `colorama`, `and google-api-python-client`.

You will need to create an Oauth2 credential in Google Cloud to let the script edit your calendar, which can be done by visiting [creating a project](https://developers.google.com/workspace/guides/create-project), enabling the Google Calendar API, and creating credentials for a Desktop Application. Make sure your scope in your credential includes `https://www.googleapis.com/auth/calendar`.

To connect your Oauth2 credential to your computer download `credentials.json`. Create a file named `cal.json` with the Google Calendar ID of the calendar you want to add to in this format:

```json
{
"calendarId": "<id here>"
}
```

Or, alternatively, if you'd like to add to your main calendar, set `calendarId` to `main`.

Then, run events.py, give calendar access to your program, and watch as all events are added to your calendar.

### Example

```
>>> python event.py
    On page 1
    Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...
    Event created: Astronomy and Astrophysics Seminar: Large Scale Structure Beyond the 2-Point Function
    Event created: Condensed and Living Matter Seminar: "Interlayer Excitons and Magneto-Exciton Condensation in van der Waals Heterostructures"
    Event created: HET Seminar: Peter Adshead (University of Illinois at Urbana-Champaign)
    Event created: Physics and Astronomy Colloquium: "Biological tissues as mechanical metamaterials"
    Event created: HET Seminar: Manki Kim (MIT)
    Event created: Astronomy and Astrophysics Seminar: Meng-Xiang Lin (Chicago)
    Event created: Condensed and Living Matter Seminar: "Quantum optics meets correlated electrons"
    Event created: HET Seminar: Yifan Wang (Harvard)
    Event created: Condensed and Living Matter Seminar: "Twisting nodal superconductors"
    Event created: HET Seminar: David E. Kaplan (JHU)
    On page 2
    Event created: Astronomy and Astrophysics Seminar: Jose Maria Ezquiaga (Chicago)
    Event created: Condensed and Living Matter Seminar: "TBA"
    Event created: HET Seminar: An Introduction to the Lattice-Continuum Correspondence
    ...
    28 events created! Final date is 2022-09-21 15:30:00
```
