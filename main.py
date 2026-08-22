import json
import os
import requests
from datetime import datetime, timezone


# =========================
# ANIMAL HOSPITAL
# =========================

UNIVERSE_ID = "10148749921"

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]


# =========================
# ROBLOX API
# =========================

API_URL = (
    "https://apis.roblox.com/virtual-events/v1/"
    f"universes/{UNIVERSE_ID}/virtual-events"
)


# =========================
# STATE FILES
# =========================

EVENTS_STATE_FILE = "events_state.json"
ALERTS_STATE_FILE = "alerts_state.json"


# =========================
# JSON FUNCTIONS
# =========================

def load_json(filename, default):

    if not os.path.exists(filename):
        return default

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_json(filename, data):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================
# GET ROBLOX EVENTS
# =========================

def get_events():

    events = []

    cursor = ""

    while True:

        params = {}

        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        events.extend(
            data.get(
                "data",
                []
            )
        )

        cursor = data.get(
            "nextPageCursor"
        )

        if not cursor:
            break

    return events


# =========================
# TIME
# =========================

def parse_time(value):

    if not value:
        return None

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00"
        )
    )


# =========================
# SEND DISCORD
# =========================

def send_to_discord(
    event,
    message
):

    event_id = event["id"]

    title = (
        event.get("displayTitle")
        or event.get("title")
        or "Animal Hospital Event"
    )

    subtitle = (
        event.get("displaySubtitle")
        or event.get("subtitle")
        or ""
    )

    description = (
        event.get("displayDescription")
        or event.get("description")
        or ""
    )

    event_time = event.get(
        "eventTime",
        {}
    )

    start = event_time.get(
        "startUtc"
    )

    end = event_time.get(
        "endUtc"
    )

    event_url = (
        f"https://www.roblox.com/events/{event_id}"
    )

    fields = []

    if subtitle:

        fields.append({
            "name": "Details",
            "value": subtitle[:1024],
            "inline": False
        })

    if start:

        start_timestamp = int(
            parse_time(
                start
            ).timestamp()
        )

        fields.append({
            "name": "Starts",
            "value": (
                f"<t:{start_timestamp}:F>"
            ),
            "inline": True
        })

    if end:

        end_timestamp = int(
            parse_time(
                end
            ).timestamp()
        )

        fields.append({
            "name": "Ends",
            "value": (
                f"<t:{end_timestamp}:F>"
            ),
            "inline": True
        })

    embed = {

        "title": title,

        "url": event_url,

        "description": (
            description[:4096]
        ),

        "fields": fields,

        "footer": {
            "text": "Animal Hospital (Anomaly)"
        }
    }

    payload = {

        "username": "Animal Hospital",

        "content": message,

        "embeds": [
            embed
        ]
    }

    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    print(
        "Discord message sent successfully."
    )


# =========================
# NEW EVENT
# =========================

def send_new_event(event):

    title = (
        event.get("displayTitle")
        or event.get("title")
        or "New Event"
    )

    send_to_discord(

        event,

        (
            "📢 **NEW EVENT!**\n"
            f"**{title}**"
        )
    )

    print(
        f"New event announced: {event['id']}"
    )


# =========================
# ALERTS
# =========================

def send_alert(
    event,
    alert_type
):

    title = (
        event.get("displayTitle")
        or event.get("title")
        or "Animal Hospital Event"
    )

    messages = {

        "1h": (
            "🟡 **EVENT STARTING IN 1 HOUR!**\n"
            f"**{title}**"
        ),

        "15m": (
            "🟠 **EVENT STARTING IN 15 MINUTES!**\n"
            f"**{title}**"
        ),

        "start": (
            "🔴 **EVENT IS LIVE NOW!**\n"
            f"**{title}**"
        )
    }

    send_to_discord(
        event,
        messages[alert_type]
    )

    print(
        f"Sent {alert_type} alert "
        f"for event {event['id']}"
    )


# =========================
# CHECK ALERTS
# =========================

def check_alerts(
    events,
    alerts_state
):

    now = datetime.now(
        timezone.utc
    )

    for event in events:

        event_id = str(
            event["id"]
        )

        event_time = event.get(
            "eventTime",
            {}
        )

        start = parse_time(
            event_time.get(
                "startUtc"
            )
        )

        end = parse_time(
            event_time.get(
                "endUtc"
            )
        )

        if not start:
            continue

        # Ignore ended events

        if end and now >= end:
            continue

        if event_id not in alerts_state:

            alerts_state[event_id] = []

        sent_alerts = (
            alerts_state[event_id]
        )

        seconds_until_start = (
            start - now
        ).total_seconds()


        # =====================
        # 1 HOUR
        # =====================

        if (

            "1h" not in sent_alerts

            and

            0 < seconds_until_start <= 3600

        ):

            send_alert(
                event,
                "1h"
            )

            sent_alerts.append(
                "1h"
            )


        # =====================
        # 15 MINUTES
        # =====================

        if (

            "15m" not in sent_alerts

            and

            0 < seconds_until_start <= 900

        ):

            send_alert(
                event,
                "15m"
            )

            sent_alerts.append(
                "15m"
            )


        # =====================
        # START
        # =====================

        if (

            "start" not in sent_alerts

            and

            seconds_until_start <= 0

        ):

            send_alert(
                event,
                "start"
            )

            sent_alerts.append(
                "start"
            )

    return alerts_state


# =========================
# MAIN
# =========================

def main():

    print(
        "Checking Animal Hospital events..."
    )

    events = get_events()

    print(
        f"Found {len(events)} events."
    )

    events_state = load_json(
        EVENTS_STATE_FILE,
        None
    )

    alerts_state = load_json(
        ALERTS_STATE_FILE,
        {}
    )

    current_ids = {

        str(event["id"])

        for event in events

    }


    # =========================
    # NEW EVENTS
    # =========================

    if events_state is None:

        save_json(

            EVENTS_STATE_FILE,

            {
                "event_ids": sorted(
                    current_ids
                )
            }

        )

        print(
            "First run: "
            "existing events saved."
        )

    else:

        old_ids = set(

            events_state.get(
                "event_ids",
                []
            )

        )

        new_events = [

            event

            for event in events

            if str(event["id"])
            not in old_ids

        ]

        new_events.sort(

            key=lambda event:

            event.get(
                "createdUtc",
                ""
            )

        )

        for event in new_events:

            send_new_event(
                event
            )

        save_json(

            EVENTS_STATE_FILE,

            {
                "event_ids": sorted(
                    current_ids
                )
            }

        )

        print(
            "New events announced: "
            f"{len(new_events)}"
        )


    # =========================
    # ALERTS
    # =========================

    alerts_state = check_alerts(

        events,

        alerts_state

    )

    save_json(

        ALERTS_STATE_FILE,

        alerts_state

    )

    print(
        "Animal Hospital "
        "event check completed."
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":

    main()
