import json
import os
import requests
from datetime import datetime, timezone


# ============================================================
# CONFIG
# ============================================================

UNIVERSE_ID = "10148749921"

# Place ID of Animal Hospital
PLACE_ID = "78515283254292"

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

EVENTS_API_URL = (
    "https://apis.roblox.com/virtual-events/v1/"
    f"universes/{UNIVERSE_ID}/virtual-events"
)

THUMBNAIL_API_URL = (
    "https://thumbnails.roblox.com/v1/games/icons"
)

EVENTS_STATE_FILE = "events_state.json"
ALERTS_STATE_FILE = "alerts_state.json"


# ============================================================
# ANIMAL HOSPITAL IMAGE
# ============================================================

def get_game_thumbnail():

    try:

        response = requests.get(
            THUMBNAIL_API_URL,
            params={
                "universeIds": UNIVERSE_ID,
                "returnPolicy": "PlaceHolder",
                "size": "512x512",
                "format": "Png",
                "isCircular": "false"
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        items = data.get(
            "data",
            []
        )

        if items:

            image_url = items[0].get(
                "imageUrl"
            )

            if image_url:
                return image_url

    except Exception as error:

        print(
            "Could not get game thumbnail:",
            error
        )

    return None


# ============================================================
# JSON STORAGE
# ============================================================

def load_json(filename, default):

    if not os.path.exists(filename):
        return default

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"Could not read {filename}:",
            error
        )

        return default


def save_json(filename, data):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# ROBLOX EVENTS
# ============================================================

def get_events():

    events = []
    cursor = ""

    while True:

        params = {}

        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            EVENTS_API_URL,
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


# ============================================================
# TIME
# ============================================================

def parse_time(value):

    if not value:
        return None

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00"
        )
    )


def discord_timestamp(value):

    parsed = parse_time(value)

    if not parsed:
        return None

    return int(
        parsed.timestamp()
    )


# ============================================================
# EVENT DATA
# ============================================================

def event_title(event):

    return (
        event.get("displayTitle")
        or event.get("title")
        or "Animal Hospital Event"
    )


def event_description(event):

    return (
        event.get("displayDescription")
        or event.get("description")
        or ""
    )


def event_subtitle(event):

    return (
        event.get("displaySubtitle")
        or event.get("subtitle")
        or ""
    )


# ============================================================
# DISCORD MESSAGE
# ============================================================

def send_to_discord(
    event,
    alert_type,
    game_thumbnail
):

    event_id = event["id"]

    title = event_title(event)

    description = event_description(event)

    subtitle = event_subtitle(event)

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

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = {

        "new": {
            "emoji": "🆕",
            "title": "NEW EVENT DETECTED",
            "color": 0x58A6FF
        },

        "1h": {
            "emoji": "🟡",
            "title": "EVENT IN 1 HOUR",
            "color": 0xF1C40F
        },

        "15m": {
            "emoji": "🟠",
            "title": "EVENT IN 15 MINUTES",
            "color": 0xE67E22
        },

        "start": {
            "emoji": "🚨",
            "title": "EVENT IS LIVE",
            "color": 0xE74C3C
        }
    }

    current = status.get(
        alert_type,
        status["new"]
    )

    # --------------------------------------------------------
    # FIELDS
    # --------------------------------------------------------

    fields = []

    if start:

        timestamp = discord_timestamp(
            start
        )

        if timestamp:

            fields.append({
                "name": "🗓️ START",
                "value": (
                    f"<t:{timestamp}:F>\n"
                    f"<t:{timestamp}:R>"
                ),
                "inline": True
            })

    if end:

        timestamp = discord_timestamp(
            end
        )

        if timestamp:

            fields.append({
                "name": "⏱️ END",
                "value": (
                    f"<t:{timestamp}:F>\n"
                    f"<t:{timestamp}:R>"
                ),
                "inline": True
            })

    if subtitle:

        fields.append({
            "name": "📋 INFORMATION",
            "value": subtitle[:1024],
            "inline": False
        })

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description_text = (
        f"## {title}\n\n"
    )

    if description:

        description_text += (
            f"{description[:3000]}\n\n"
        )

    if alert_type == "start":

        description_text += (
            "🐾 **The event is happening now!**"
        )

    elif alert_type == "1h":

        description_text += (
            "🩺 **Prepare for the event.**"
        )

    elif alert_type == "15m":

        description_text += (
            "🚨 **Get ready! The event starts soon.**"
        )

    else:

        description_text += (
            "📋 **A new event has been detected.**"
        )

    # --------------------------------------------------------
    # EMBED
    # --------------------------------------------------------

    embed = {

        "author": {
            "name": (
                "🏥 ANIMAL HOSPITAL"
            )
        },

        "title": (
            f"{current['emoji']} "
            f"{current['title']}"
        ),

        "url": event_url,

        "description": description_text,

        "color": current["color"],

        "fields": fields,

        "footer": {
            "text": (
                "Animal Hospital (Anomaly) • "
                "Roblox Event Monitor"
            )
        },

        "timestamp": (
            datetime.now(
                timezone.utc
            ).isoformat()
        )
    }

    # --------------------------------------------------------
    # GAME IMAGE
    # --------------------------------------------------------

    if game_thumbnail:

        embed["thumbnail"] = {
            "url": game_thumbnail
        }

    # --------------------------------------------------------
    # DISCORD PAYLOAD
    # --------------------------------------------------------

    payload = {

        "username": (
            "🏥 Animal Hospital"
        ),

        "content": (
            f"🏥 **ANIMAL HOSPITAL**\n"
            f"{current['emoji']} "
            f"**{current['title']}**"
        ),

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
        f"Discord notification sent: "
        f"{alert_type} | {event_id}"
    )


# ============================================================
# NEW EVENTS
# ============================================================

def check_new_events(
    events,
    events_state,
    game_thumbnail
):

    current_ids = {

        str(event["id"])

        for event in events

    }

    # --------------------------------------------------------
    # FIRST RUN
    # --------------------------------------------------------

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
            f"First run: saved "
            f"{len(current_ids)} existing events."
        )

        return

    # --------------------------------------------------------
    # OLD EVENTS
    # --------------------------------------------------------

    old_ids = set(

        events_state.get(
            "event_ids",
            []
        )

    )

    # --------------------------------------------------------
    # NEW EVENTS
    # --------------------------------------------------------

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

        send_to_discord(
            event,
            "new",
            game_thumbnail
        )

    print(
        f"New events: "
        f"{len(new_events)}"
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_json(

        EVENTS_STATE_FILE,

        {
            "event_ids": sorted(
                current_ids
            )
        }

    )


# ============================================================
# ALERT SYSTEM
# ============================================================

def check_alerts(
    events,
    alerts_state,
    game_thumbnail
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

        # Ignore finished events

        if end and now >= end:
            continue

        if event_id not in alerts_state:

            alerts_state[event_id] = []

        sent = alerts_state[
            event_id
        ]

        seconds_until_start = (
            start - now
        ).total_seconds()

        # ----------------------------------------------------
        # 1 HOUR
        # ----------------------------------------------------

        if (

            "1h" not in sent

            and

            0 < seconds_until_start <= 3600

        ):

            send_to_discord(
                event,
                "1h",
                game_thumbnail
            )

            sent.append(
                "1h"
            )

        # ----------------------------------------------------
        # 15 MINUTES
        # ----------------------------------------------------

        if (

            "15m" not in sent

            and

            0 < seconds_until_start <= 900

        ):

            send_to_discord(
                event,
                "15m",
                game_thumbnail
            )

            sent.append(
                "15m"
            )

        # ----------------------------------------------------
        # LIVE
        # ----------------------------------------------------

        if (

            "start" not in sent

            and

            seconds_until_start <= 0

        ):

            send_to_discord(
                event,
                "start",
                game_thumbnail
            )

            sent.append(
                "start"
            )

    return alerts_state


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "🏥 ANIMAL HOSPITAL EVENT MONITOR"
    )

    print(
        "========================================"
    )

    print(
        f"Universe: {UNIVERSE_ID}"
    )

    # --------------------------------------------------------
    # Game thumbnail
    # --------------------------------------------------------

    game_thumbnail = get_game_thumbnail()

    if game_thumbnail:

        print(
            "Game thumbnail: FOUND"
        )

    else:

        print(
            "Game thumbnail: NOT FOUND"
        )

    # --------------------------------------------------------
    # Events
    # --------------------------------------------------------

    events = get_events()

    print(
        f"Events found: {len(events)}"
    )

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    events_state = load_json(
        EVENTS_STATE_FILE,
        None
    )

    alerts_state = load_json(
        ALERTS_STATE_FILE,
        {}
    )

    # --------------------------------------------------------
    # New events
    # --------------------------------------------------------

    check_new_events(
        events,
        events_state,
        game_thumbnail
    )

    # --------------------------------------------------------
    # Alerts
    # --------------------------------------------------------

    alerts_state = check_alerts(
        events,
        alerts_state,
        game_thumbnail
    )

    save_json(
        ALERTS_STATE_FILE,
        alerts_state
    )

    print(
        "========================================"
    )

    print(
        "✅ CHECK COMPLETED"
    )

    print(
        "========================================"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
