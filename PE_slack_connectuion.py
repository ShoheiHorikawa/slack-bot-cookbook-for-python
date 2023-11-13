from datetime import datetime
import requests
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

with open("slack_bot_token.txt") as f:
    slack_bot_token = f.read()
app = App(token=slack_bot_token)

with open("slack_app_token.txt") as f:
    slack_app_token = f.read()

with open("pe_api_key.txt") as f:
    pe_api_key = f.read()


# 初期画面
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    publish_initial_view(client, event["user"], logger)


# 初期画面定義部分
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
                        "text": {"type": "mrkdwn", "text": "スケジュールに関して以下の機能を選択してください："},
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "radio_buttons",
                                "options": [
                                    {
                                        "text": {"type": "plain_text", "text": "確認(1ユーザ)"},
                                        "value": "check"
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "登録"},
                                        "value": "register"
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "アイテイルトコ"},
                                        "value": "multi_check"
                                    },
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


# ラジオボタン入れ子部分
@app.action("selection_action")
def handle_selection_action(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    selection = body["actions"][0]["selected_option"]["value"]

    if selection == "check":
        blocks = get_schedule_blocks()
    elif selection == "register":
        blocks = post_schedule_blocks()
    elif selection == "multi_check":
        blocks = get_multi_schedule_blocks()

    blocks.append(get_back_button_block())
    client.views_publish(
        user_id=user_id,
        view={"type": "home", "blocks": blocks}
    )


# [戻る]ボタンブロック
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


# [戻るボタン]アクション定義
@app.action("back_button")
def handle_back_button(ack, body, client, logger):
    ack()
    publish_initial_view(client, body["user"]["id"], logger)


# スケジュール確認ブロック
def get_schedule_blocks():
    return [
        # 日付選択器のブロック
        {
            "type": "section",
            "block_id": "user_select_block",
            "text": {
                "type": "mrkdwn",
                "text": "スケジュールを確認するユーザーを選択してください："
            },
            "accessory": {
                "type": "users_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "ユーザーを選択",
                    "emoji": True
                },
            "action_id": "user_select_action"
            }
        },
        # 日付選択器のブロック
        {
            "type": "input",
            "block_id": "date_select_block",
            "element": {
                "type": "datepicker",
                "initial_date": "2023-01-01",
                "action_id": "date_selected"
            },
            "label": {
                "type": "plain_text",
                "text": "日付を選択してください"
            }
        },
        # 確認ボタンのブロック
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "確認"
                    },
                    "value": "confirm",
                    "action_id": "confirm_schedule"
                }
            ]
        }
    ]


# スケジュール登録ブロック
def post_schedule_blocks():
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


#
def get_multi_schedule_blocks():
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




# スケジュール確認機能
@app.action("confirm_schedule")
def handle_confirm_schedule(ack, body, logger, client):
    ack()
    action_user_id = body["user"]["id"]
    selected_user_id = body["view"]["state"]["values"]["user_select_block"]["user_select_action"]["selected_user"]
    selected_date = body["view"]["state"]["values"]["date_select_block"]["date_selected"]["selected_date"]

    # ユーザー情報取得と社員番号の取得を関数化
    emp_code = get_employee_code(client, selected_user_id, logger)
    if emp_code:
        schedule_text = get_power_egg_schedule(emp_code, selected_date, logger)
        client.chat_postMessage(
            channel=action_user_id,
            text=schedule_text
        )
    else:
        client.chat_postMessage(
            channel=action_user_id,
            text="適切な社員番号またはスケジュール情報が見つかりませんでした。"
        )

def get_employee_code(client, user_id, logger):
    user_info_response = client.users_info(user=user_id)
    if user_info_response["ok"]:
        user_email = user_info_response["user"]["profile"].get("email")
        if user_email:
            email_prefix = user_email.split('@')[0]
            emp_code_url = f"http://192.168.254.101/pe4j/api/rest/v1/xdb/q/records.json?database=情報システム管理/全社共通IT/【極秘】E-mailアカウント管理&query=[{{\"items\":[{{\"field\":\"メールアドレス\",\"opr\":\"=\",\"value\":\"{email_prefix}\"}}]}}]"
            emp_code_response = requests.get(emp_code_url, headers={'X-API-Key': pe_api_key})
            emp_code_data = json.loads(emp_code_response.text)
            if emp_code_data["count"] > 0:
                emp_code = str(emp_code_data["records"][0]["社員番号"]["value"])
                return "0" + emp_code if len(emp_code) == 5 else emp_code
    logger.error(f"Failed to retrieve user info: {user_info_response.get('error', 'Unknown error')}")
    return None

def get_power_egg_schedule(emp_code, date, logger):
    url = "http://192.168.254.101/pe4j/api/rest/v1/schedule/schedules.json"
    headers={'X-API-Key': pe_api_key}
    params = {
        "corpId": "380050117",
        "empCode": emp_code,
        "fromDate": date,
        "toDate": date,
        "needParticipantName": 0,
        "needResourceName": 0,
        "includingNonParticipation": 0,
    }
    schedule_response = requests.get(url, headers=headers, params=params)
    if schedule_response.ok:
        data = schedule_response.json()
        total_schedules = data["count"]
        private_schedules = sum([1 for s in data["schedules"] if s["publicState"] == 0])
        schedule_texts = [f"{format_time_range(s)} ：{'非公開スケジュール' if s['publicState'] == 0 else s['subject']}" for s in data["schedules"]]
        return f"{date}のスケジュールは{total_schedules}件あります。その中で非公開スケジュールは{private_schedules}件あります。\n" + "\n".join(schedule_texts)
    logger.error("Failed to get schedule from PowerEgg API.")
    return "スケジュール情報の取得に失敗しました。"

def format_time_range(schedule):
    return f"{schedule['fromTime'][:2]}:{schedule['fromTime'][2:]}-{schedule['toTime'][:2]}:{schedule['toTime'][2:]}"


@app.action("user_select_action")
def handle_user_selected(ack, body, logger):
    ack()  # イベントの確認
    logger.info(body)  # ログ出力（必要に応じて）


# メイン部分
if __name__ == "__main__":
    SocketModeHandler(app, slack_app_token).start()