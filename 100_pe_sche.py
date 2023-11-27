from datetime import datetime
import requests
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, filename='bot_log.log', format='%(asctime)s - %(levelname)s - %(message)s')

# 設定ファイルの読み込み
with open("config.json", encoding="utf-8") as config_file:
    config = json.load(config_file)

slack_app_token = config["slack_app_token"]
slack_bot_token = config["slack_bot_token"]
pe_api_key = config["pe_api_key"]
corp_id = config["corp_id"]
get_schedule_url = config["get_schedule"]
post_schedule_url = config["post_schedule"]
get_empCode_url = config["get_empCode"]
ALLOWED_USER_IDS = config["allowed_user_ids"]

app = App(token=slack_bot_token)


# ユーザー名を取得する関数
def get_user_name(client, user_id, logger):
    try:
        response = client.users_info(user=user_id)
        if response["ok"]:
            return response["user"]["real_name"]
        else:
            logger.error(f"Failed to get user info: {response['error']}")
            return "Unknown User"
    except Exception as e:
        logger.error(f"Error while getting user info: {e}")
        return "Unknown User"


# ログ記録関数
def log_user_action(user_name, action, status="Success", details=""):
    logging.info(f"User Action - User Name: {user_name}, Action: {action}, Status: {status}, Details: {details}")


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
                        "text": {
                            "type": "mrkdwn",
                            "text": "🔰*HOW_TO_USE* | 使い方やアプリ情報は 【ワークスペース情報】タブ を参照してね！"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "\n"
                        }
                    },
                    {
		            	"type": "divider"
		            },
                    {
                    "type": "rich_text",
                    "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": "好きな機能を下から選んでね"
                                    },
                                    {
                                        "type": "emoji",
                                        "name": "t-rex"
                                    },                                    
                                ]
                            }
                        ]   
		            },
                    {
		            	"type": "divider"
		            },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "radio_buttons",
                                "options": [
                                    {
                                        "text": {"type": "plain_text", "text": "確認(1ユーザ)🦖"},
                                        "value": "check"
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "確認(複数ユーザ)🦖🦕"},
                                        "value": "multi_check"
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "登録🕒"},
                                        "value": "register"
                                    },
                                ],
                                "action_id": "selection_action"
                            }
                        ]
                    },
                    {
		            	"type": "divider"
		            },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Presented by _NIKKO_ _AI_"
                        }
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

    if user_id not in ALLOWED_USER_IDS:
        ack("このコマンドは特定のユーザーに限定されています。")
        client.chat_postMessage(
            channel=user_id,
            text="このコマンドは特定のユーザーに限定されています。"
        )
        return

    if selection == "check":
        blocks = get_schedule_blocks()
    elif selection == "multi_check":
        blocks = get_multi_user_schedule_blocks()
    elif selection == "register":
        blocks = post_schedule_blocks()

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
    current_date = datetime.now().strftime('%Y-%m-%d')
    return [
        # ユーザ選択器のブロック
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
                "initial_date": current_date,
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


# 複数ユーザーのスケジュール確認ブロック
def get_multi_user_schedule_blocks():
    current_date = datetime.now().strftime('%Y-%m-%d')
    return [
        # 複数ユーザー選択のブロック
        {
            "type": "section",
            "block_id": "multi_user_select_block",
            "text": {
                "type": "mrkdwn",
                "text": "スケジュールを確認するユーザー（複数選択可能）を選択してください："
            },
            "accessory": {
                "type": "multi_users_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "ユーザーを選択",
                    "emoji": True
                },
            "action_id": "multi_user_select_action"
            }
        },
        # 日付選択器のブロック
        {
            "type": "input",
            "block_id": "date_select_block",
            "element": {
                "type": "datepicker",
                "initial_date": current_date,
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
                    "value": "confirm_multi",
                    "action_id": "confirm_multi_schedule"
                }
            ]
        }
    ]


# スケジュール登録ブロック
def post_schedule_blocks():
    current_date = datetime.now().strftime('%Y-%m-%d')
    return [
        # 日付選択
        {
            "type": "input",
            "block_id": "date_select_block",
            "element": {"type": "datepicker", "action_id": "date_selected", "initial_date": current_date,},
            "label": {"type": "plain_text", "text": "日付を選択してください"}
        },
        # 件名入力
        {
            "type": "input",
            "block_id": "subject_input_block",
            "element": {"type": "plain_text_input", "action_id": "subject_input"},
            "label": {"type": "plain_text", "text": "件名"}
        },
        # 予定区分選択
        {
            "type": "input",
            "block_id": "plan_class_select_block",
            "element": {
                "type": "static_select",
                "placeholder": {"type": "plain_text", "text": "予定区分を選択"},
                "options": [
                    {"text": {"type": "plain_text", "text": "ー"}, "value": "0"},
                    {"text": {"type": "plain_text", "text": "社内会議"}, "value": "1"},
                    {"text": {"type": "plain_text", "text": "訪問"}, "value": "2"},
                    {"text": {"type": "plain_text", "text": "社内"}, "value": "3"},
                    {"text": {"type": "plain_text", "text": "来客"}, "value": "4"},
                    {"text": {"type": "plain_text", "text": "出張"}, "value": "5"},
                    {"text": {"type": "plain_text", "text": "休暇"}, "value": "6"},
                    {"text": {"type": "plain_text", "text": "その他"}, "value": "7"},
                    {"text": {"type": "plain_text", "text": "テレワーク"}, "value": "17"}
                            ],
                "initial_option": {"text": {"type": "plain_text", "text": "ー"}, "value": "0"},
                "action_id": "plan_class_selected"
            },
            "label": {"type": "plain_text", "text": "予定区分"}
        },
        # 開始時間選択
        {
            "type": "input",
            "block_id": "start_time_select_block",
            "element": {"type": "timepicker", "action_id": "start_time_selected"},
            "label": {"type": "plain_text", "text": "開始時間"}
        },
        # 終了時間選択
        {
            "type": "input",
            "block_id": "end_time_select_block",
            "element": {"type": "timepicker", "action_id": "end_time_selected"},
            "label": {"type": "plain_text", "text": "終了時間"}
        },
        # 内容入力
        {
            "type": "input",
            "block_id": "content_input_block",
            "element": {"type": "plain_text_input", "action_id": "content_input"},
            "label": {"type": "plain_text", "text": "内容"}
        },
        # 公開選択
        {
            "type": "input",
            "block_id": "public_select_block",
            "element": {
                "type": "radio_buttons",
                "options": [
                    {"text": {"type": "plain_text", "text": "公開"}, "value": "true"},
                    {"text": {"type": "plain_text", "text": "非公開"}, "value": "false"}
                ],
                "initial_option": {"text": {"type": "plain_text", "text": "公開"}, "value": "true"},
                "action_id": "public_selected"
            },
            "label": {"type": "plain_text", "text": "公開/非公開"}
        },
        # 登録ボタンのブロック
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "登録"
                    },
                    "value": "confirm",
                    "action_id": "register_schedule_button"
                }
            ]
        }
    ]


# スケジュール確認機能
@app.action("confirm_schedule")
def handle_confirm_schedule(ack, body, logger, client):
    ack()
    action_user_id = body["user"]["id"]
    user_name = get_user_name(client, action_user_id, logger)
    selected_user_id = body["view"]["state"]["values"]["user_select_block"]["user_select_action"]["selected_user"]
    selected_date = body["view"]["state"]["values"]["date_select_block"]["date_selected"]["selected_date"]

    emp_code = get_employee_code(client, selected_user_id, logger)
    if emp_code:
        schedule_text = get_power_egg_schedule(emp_code, selected_date, logger)
        user_info_response = client.users_info(user=selected_user_id)
        user_name_selected = user_info_response["user"]["real_name"] if user_info_response["ok"] else "Unknown User"
        formatted_text = f"⏱ *{user_name_selected}* ⏱\n{schedule_text}\n----------"
        client.chat_postMessage(channel=action_user_id, text=formatted_text)
        log_user_action(user_name, "Confirm Schedule", "Success", f"Date: {selected_date}, User ID: {selected_user_id}")
    else:
        client.chat_postMessage(channel=action_user_id, text="適切な社員番号またはスケジュール情報が見つかりませんでした。")
        log_user_action(user_name, "Confirm Schedule", "Failed", f"Date: {selected_date}, User ID: {selected_user_id}")


def get_employee_code(client, user_id, logger):
    user_info_response = client.users_info(user=user_id)
    if user_info_response["ok"]:
        user_email = user_info_response["user"]["profile"].get("email")
        if user_email:
            emp_code_url = get_empCode_url + f"&query=[{{\"items\":[{{\"field\":\"メールアドレス\",\"opr\":\"=\",\"value\":\"{user_email}\"}}]}}]"
            emp_code_response = requests.get(emp_code_url, headers={'X-API-Key': pe_api_key})
            emp_code_data = json.loads(emp_code_response.text)
            if emp_code_data["count"] > 0:
                emp_code = str(emp_code_data["records"][0]["社員CD"]["value"])
                return "0" + emp_code if len(emp_code) == 5 else emp_code
    logger.error(f"Failed to retrieve user info: {user_info_response.get('error', 'Unknown error')}")
    return None


def get_power_egg_schedule(emp_code, date, logger):
    url = get_schedule_url
    headers={'X-API-Key': pe_api_key}
    params = {
        "corpId": corp_id,
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
        schedule_texts = [f"【{format_time_range(s)}】 {'非公開スケジュール' if s['publicState'] == 0 else s['subject']}" for s in data["schedules"]]
        return f"{date}のスケジュールは{total_schedules}件あります。その中で非公開スケジュールは{private_schedules}件あります。\n" + "\n".join(schedule_texts)
    logger.error("Failed to get schedule from PowerEgg API.")
    return "スケジュール情報の取得に失敗しました。"


def format_time_range(schedule):
    return f"{schedule['fromTime'][:2]}:{schedule['fromTime'][2:]}-{schedule['toTime'][:2]}:{schedule['toTime'][2:]}"


@app.action("user_select_action")
def handle_user_selected(ack, body, logger):
    ack()  # イベントの確認
    logger.info(body)  # ログ出力（必要に応じて）


# 複数ユーザー選択アクションのハンドラ
@app.action("multi_user_select_action")
def handle_multi_user_select_action(ack, body, logger):
    ack()  # アクションの確認応答
    logger.info(f"Received multi user select action: {body}")  # ログに情報を記録


@app.action("confirm_multi_schedule")
def handle_confirm_multi_schedule(ack, body, logger, client):
    ack()
    action_user_id = body["user"]["id"]
    action_user_name = get_user_name(client, action_user_id, logger)
    selected_user_ids = body["view"]["state"]["values"]["multi_user_select_block"]["multi_user_select_action"]["selected_users"]
    selected_date = body["view"]["state"]["values"]["date_select_block"]["date_selected"]["selected_date"]

    user_schedule_texts = []
    unable_to_confirm_user_names = []

    for user_id in selected_user_ids:
        emp_code = get_employee_code(client, user_id, logger)
        if emp_code:
            schedule_text = get_power_egg_schedule(emp_code, selected_date, logger)
            user_name = get_user_name(client, user_id, logger)
            user_schedule_texts.append(f"⏱ *{user_name}* ⏱\n{schedule_text}\n----------")
        else:
            unable_to_confirm_user_name = get_user_name(client, user_id, logger)
            unable_to_confirm_user_names.append(unable_to_confirm_user_name)
            log_user_action(action_user_name, "Multi User Schedule Confirmation", "Failed", f"User ID: {user_id}, Date: {selected_date}")

    response_text = "\n\n".join(user_schedule_texts)
    
    if unable_to_confirm_user_names:
        unable_users_text = ", ".join(unable_to_confirm_user_names)
        response_text += f"\n\n⏱ *{unable_users_text}* はスケジュールを確認できませんでした。"

    client.chat_postMessage(channel=action_user_id, text=response_text)
    log_user_action(action_user_name, "Multi User Schedule Confirmation", "Success", f"Date: {selected_date}, User IDs: {selected_user_ids}")


# スケジュール登録機能
@app.action("register_schedule_button")
def handle_register_schedule(ack, body, logger, client):
    ack()
    action_user_id = body["user"]["id"]
    action_user_name = get_user_name(client, action_user_id, logger)
    values = body["view"]["state"]["values"]

    emp_code = get_employee_code(client, action_user_id, logger)

    date_selection = values["date_select_block"].get("date_selected")
    selected_date = date_selection.get("selected_date") if date_selection else None
    subject_input = values["subject_input_block"].get("subject_input")
    subject = subject_input.get("value") if subject_input else None

    if not emp_code or not selected_date or not subject:
        client.chat_postMessage(channel=action_user_id, text="未入力項目があります。")
        log_user_action(action_user_name, "Schedule Registration", "Failed", "Missing required fields")
        return

    plan_class_id = values["plan_class_select_block"]["plan_class_selected"]["selected_option"]["value"]
    from_time = values["start_time_select_block"]["start_time_selected"]["selected_time"] or ""
    to_time = values["end_time_select_block"]["end_time_selected"]["selected_time"] or ""
    content = values["content_input_block"]["content_input"]["value"] or ""
    is_public = values["public_select_block"]["public_selected"]["selected_option"]["value"]

    try:
        url = post_schedule_url
        headers = {"X-API-Key": pe_api_key, "Content-Type": "application/json"}
        data = {
            "corpId": corp_id, "empCode": emp_code, "fromDate": selected_date, "fromTime": from_time.replace(":", ""), "toTime": to_time.replace(":", ""), "schedulePlanClassId": plan_class_id, "subject": subject, "content": content, "isPublic": is_public,
        }
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code == 200 or "id" in response_data:
            client.chat_postMessage(channel=action_user_id, text=f"スケジュールを登録しました。ID: {response_data.get('id', '不明')}")
            log_user_action(action_user_name, "Schedule Registration", "Success", f"Registered schedule for date: {selected_date}")
        else:
            client.chat_postMessage(channel=action_user_id, text="スケジュール登録に失敗しました。")
            log_user_action(action_user_name, "Schedule Registration", "Failed", response.text)
    except Exception as e:
        client.chat_postMessage(channel=action_user_id, text="スケジュール登録中にエラーが発生しました。")
        log_user_action(action_user_name, "Schedule Registration", "Failed", str(e))


# メイン部分
if __name__ == "__main__":
    SocketModeHandler(app, slack_app_token).start()