import os
import requests
from datetime import datetime, timezone


UNIVERSE_ID = "10148749921"

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

EVENTS_API_URL = (
    "https://apis.roblox.com/virtual-events/v1/"
    f"universes/{UNIVERSE_ID}/virtual-events"
)

THUMBNAIL_API_URL = (
    "https://thumbnails.roblox.com/v1/games/icons"
)


def get_events():

    response = requests.get(
        EVENTS_API_URL,
        timeout=30
    )

    response.raise_for_status()

    return response.json().get(
        "data",
        []
    )


def get_game_thumbnail():

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

    if data.get("data"):

        return data["data"][0].get(
            "imageUrl"
        )

    return None


def send_test_message(event, thumbnail):

    title = (
        event.get("displayTitle")
        or event.get("title")
        or "Animal Hospital Event"
    )

    description = (
        event.get("displayDescription")
        or event.get("description")
        or "No description available."
    )

    event_id = event["id"]

    event_url = (
        f"https://www.roblox.com/events/{event_id}"
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

    fields = []

    if start:

        start_time = datetime.fromisoformat(
            start.replace(
                "Z",
                "+00:00"
            )
        )

        timestamp = int(
            start_time.timestamp()
        )

        fields.append({
            "name": "🗓️ START",
            "value": (
                f"<t:{timestamp}:F>\n"
                f"<t:{timestamp}:R>"
            ),
            "inline": True
        })

    if end:

        end_time = datetime.fromisoformat(
            end.replace(
                "Z",
                "+00:00"
            )
        )

        timestamp = int(
            end_time.timestamp()
        )

        fields.append({
            "name": "⏱️ END",
            "value": (
                f"<t:{timestamp}:F>\n"
                f"<t:{timestamp}:R>"
            ),
            "inline": True
        })

    embed = {

        "author": {
            "name": "🏥 ANIMAL HOSPITAL"
        },

        "title": "🚨 EVENT IS LIVE",

        "url": event_url,

        "description": (
            f"## 🐾 {title}\n\n"
            f"{description[:3000]}\n\n"
            "🚑 **The event is happening now!**"
        ),

        "color": 0xE74C3C,

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

    if thumbnail:

        embed["thumbnail"] = {
            "url": thumbnail
        }

    payload = {

        "username": "🏥 Animal Hospital",

        "content": (
            "🏥 **ANIMAL HOSPITAL**\n"
            "🚨 **EVENT IS LIVE**"
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
        "✅ Test message sent successfully!"
    )


def main():

    print(
        "🏥 Animal Hospital Webhook Test"
    )

    events = get_events()

    print(
        f"Found {len(events)} events."
    )

    if not events:

        print(
            "❌ No events found."
        )

        return

    thumbnail = get_game_thumbnail()

    # Use the currently running/first event
    event = events[0]

    print(
        "Testing event:",
        event.get(
            "displayTitle"
            or "Unknown Event"
        )
    )

    send_test_message(
        event,
        thumbnail
    )


if __name__ == "__main__":
    main()
