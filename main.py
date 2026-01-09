import os
import psycopg2
from datetime import datetime
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_token = os.getenv('SLACK_BOT_TOKEN')

client = WebClient(token=slack_token)


def send_slack_message(channel_id, blocks_msg):
    try:
        response = client.chat_postMessage(
            channel=channel_id,  # Channel ID or name (e.g., "#general")
            text="Message content",
            blocks=json.dumps(blocks_msg)
        )
        print(f"Message sent: {response['message']['text']}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")


def get_tasks():
    database_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    query = """SELECT "Task"
            FROM "MonthlySchedule" ms
            WHERE "MonthNum" = EXTRACT(MONTH FROM CURRENT_DATE)
            AND NOT EXISTS (
                SELECT 1
                FROM "TaskLog" tl
                WHERE tl."TaskId" = ms."Id"
                  AND EXTRACT(MONTH FROM tl."CompletionDate") = EXTRACT(MONTH FROM CURRENT_DATE)
                  AND EXTRACT(YEAR FROM tl."CompletionDate") = EXTRACT(YEAR FROM CURRENT_DATE)
            );"""
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    results = [task[0] for task in results]
    return results


def generate_slack_blocks(data, header):
    """
    Generate a Slack block JSON structure for savings data.
    """
    blocks = [{
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"Current {header} Maintenance Tasks"
        }
    }, {"type": "divider"}]

    # Add the data rows
    for task in data:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": task
            }
        })
        blocks.append({"type": "divider"})

    # Footer link
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "To update tasks, please visit <https://mcl-maintain.up.railway.app/|this page>."
        }
    })

    return blocks


def is_first_or_third_saturday():
    today = datetime.now()
    if today.weekday() != 5:  # 5 = Saturday
        return False
    day = today.day
    # First Saturday: day 1-7, Third Saturday: day 15-21
    return day <= 7 or (15 <= day <= 21)


def main():
    if not is_first_or_third_saturday():
        print("Not the 1st or 3rd Saturday. Skipping.")
        return

    tasks = get_tasks()
    if not tasks:
        print("No pending tasks for this month.")
        return

    slack_blocks = generate_slack_blocks(tasks, datetime.now().strftime("%B"))
    send_slack_message("C01EUJYV2JV", slack_blocks)


if __name__ == "__main__":
    main()
