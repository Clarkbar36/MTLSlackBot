import sqlite3
import os
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
    database_file = 'MTLmaintenance.db'
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    query = f"SELECT Task FROM MonthlySchedule WHERE MonthNum = strftime('%m', 'now');"
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
            "text": f"{header} Maintenance Tasks"
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

    return blocks


def lambda_handler(event, context):
    # Query for month's tasks
    tasks = get_tasks()

    # Generate Slack message blocks
    slack_blocks = generate_slack_blocks(tasks, datetime.now().strftime("%B"))

    # Send the message to Slack
    send_slack_message("C01EUJYV2JV", slack_blocks)  # maintenance -  C06A231G3E3

    return {
        "statusCode": 200,
        "body": json.dumps("Message sent successfully")
    }
