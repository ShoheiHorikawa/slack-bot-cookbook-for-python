from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

with open("slack_bot_token.txt") as f:
    slack_bot_token = f.read()
app = App(token=slack_bot_token)

with open("slack_app_token.txt") as f:
    slack_app_token = f.read()


@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    publish_initial_view(client, event["user"], logger)

def publish_initial_view(client, user_id, logger):
    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": [
                    # ラジオボタンのブロック
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "選択してください："},
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "radio_buttons",
                                "options": [
                                    {
                                        "text": {"type": "plain_text", "text": "日程"},
                                        "value": "schedule"
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "ユーザー"},
                                        "value": "user"
                                    }
                                ],
                                "action_id": "selection_action"
                            }
                        ]
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

@app.action("selection_action")
def handle_selection_action(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    selection = body["actions"][0]["selected_option"]["value"]

    if selection == "schedule":
        blocks = get_schedule_blocks()
    elif selection == "user":
        blocks = get_user_blocks()

    blocks.append(get_back_button_block())
    client.views_publish(
        user_id=user_id,
        view={"type": "home", "blocks": blocks}
    )

def get_schedule_blocks():
    return [
        # 日付選択器のブロック
        {
            "type": "input",
            "block_id": "date_block",
            "element": {
                "type": "datepicker",
                "initial_date": "2023-01-01",
                "action_id": "date_input"
            },
            "label": {
                "type": "plain_text",
                "text": "日付を選択してください"
            }
        }
    ]

def get_user_blocks():
    return [
        # ユーザー選択メニューのブロック
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "ユーザーを選択してください："
            },
            "accessory": {
                "type": "users_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "ユーザーを選択",
                    "emoji": True
                },
                "action_id": "users_select_action"
            }
        }
    ]

def get_back_button_block():
    return {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "戻る"},
                "value": "back",
                "action_id": "back_button"
            }
        ]
    }

@app.action("back_button")
def handle_back_button(ack, body, client, logger):
    ack()
    publish_initial_view(client, body["user"]["id"], logger)


@app.action("users_select_action")
def handle_users_select_action(ack, body, logger, client):
    ack()
    user_id = body["user"]["id"]
    selected_user = body["actions"][0]["selected_user"]

    logger.info(f"User {user_id} has selected user {selected_user}")

    client.chat_postMessage(
        channel=user_id,
        text=f"あなたはユーザー {selected_user} を選択しました。"
    )

if __name__ == "__main__":
    SocketModeHandler(app, slack_app_token).start()