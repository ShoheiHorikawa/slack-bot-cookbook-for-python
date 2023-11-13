from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

with open("slack_bot_token.txt") as f:
    slack_bot_token = f.read()
app = App(token=slack_bot_token)

with open("slack_app_token.txt") as f:
    slack_app_token = f.read()


@app.event("app_home_opened")
def home_tab_ui(client, event, logger):
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        client.views_publish(
            user_id = event["user"],
            view = {
                "type": "home",
                "callback_id": "home_view",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": f"こんにちは！今日は{today}です！今日も張り切って頑張りましょう！",
                            "emoji": True
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "date_block",
                        "element": {
                            "type": "datepicker",
                            "initial_date": "2023-11-13",
                            "action_id": "date_input"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "日付を選択してください"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "以下はユーザー(単一)選択です。選択すると、選択したユーザーの名前とアドレスが送信されます。",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "ユーザーを選択してください。"
                        },
                        "accessory": {
                            "type": "users_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a user",
                                "emoji": True
                            },
                        "action_id": "users_select_action"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "以下はユーザー(複数)選択です。選択すると、選択したユーザーの名前とアドレスが送信されます。",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "ユーザーを選択してください。"
                        },
                        "accessory": {
                            "type": "multi_users_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a user",
                                "emoji": True
                            },
                        "action_id": "multi_users_select_action"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "以下はラジオボタン選択による入れ子構造です。",
                            "emoji": True
                        }
                    },
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
                    },
                ]
            }
        )
    
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


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


### これは上と同じで、選択するとbotから選択したユーザのidが返されます
# @app.action("multi_users_select-action")
# def handle_users_select_action(ack, client, body, logger):
#     ack()
#     action_user_id = body["user"]["id"]
#     selected_users = body["actions"][0]["selected_users"]  # 選択されたユーザーのIDリスト

#     # 選択されたユーザーに関する処理
#     # 例: 選択されたユーザーの情報を取得したり、特定のメッセージを送信したりする
#     # ...

#     # 確認のメッセージを送信
#     client.chat_postMessage(
#         channel=action_user_id,
#         text=f"選択されたユーザー: {', '.join(selected_users)}"
#     )


@app.action("multi_users_select_action")
def handle_multi_users_select(ack, body, logger, client):
    ack()
    action_user_id = body["user"]["id"]
    selected_users = body["actions"][0]["selected_users"]

    valid_users_info = []
    invalid_users_info = []
    for user_id in selected_users:
        user_info_response = client.users_info(user=user_id)
        if user_info_response["ok"]:
            user_info = user_info_response["user"]
            user_name = user_info["real_name"]

            # Eメールアドレスが存在するか確認
            user_email = user_info["profile"].get("email")
            if user_email and "@nikko-company.co.jp" in user_email:
                valid_users_info.append(f"{user_name} ({user_email})")
            else:
                invalid_users_info.append(f"{user_name} ({user_email if user_email else 'Eメールなし'})")
        else:
            logger.error(f"Failed to retrieve user info: {user_info_response['error']}")


    # 有効なユーザー情報を表示
    valid_users_info_str = "\n".join(valid_users_info)
    invalid_users_info_str = "\n".join(invalid_users_info)
    response_text = f"選択された有効なユーザー:\n{valid_users_info_str}"

    # 無効なユーザーが存在する場合、その情報も表示
    if invalid_users_info:
        response_text += f"\n\n以下のアカウントは正常に登録されていません：\n{invalid_users_info_str}"

    client.chat_postMessage(
        channel=action_user_id,
        text=response_text
    )


@app.action("selection_action")
def handle_selection_action(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    selection = body["actions"][0]["selected_option"]["value"]

    if selection == "schedule":
        # 日程選択ビューを表示
        blocks = [
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
    elif selection == "user":
        # ユーザー選択ビューを表示
        blocks = [
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

    client.views_publish(
        user_id=user_id,
        view={
            "type": "home",
            "blocks": blocks
        }
    )


if __name__ == "__main__":
    SocketModeHandler(app, slack_app_token).start()