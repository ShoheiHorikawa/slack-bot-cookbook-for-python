from datetime import datetime
import requests
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# with open("slack_bot_token.txt") as f:
#     slack_bot_token = f.read()
# app = App(token=slack_bot_token)

# with open("slack_app_token.txt") as f:
#     slack_app_token = f.read()

# with open("pe_api_key.txt") as f:
#     pe_api_key = f.read()

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

app = App(token=slack_bot_token)

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
                                    # {
                                    #     "text": {"type": "plain_text", "text": "アイトルトコ"},
                                    #     "value": "multi_check"
                                    # },
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
    # elif selection == "multi_check":
    #     blocks = get_multi_schedule_blocks()

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


# スケジュール登録ブロック
def post_schedule_blocks():
    current_date = datetime.now().strftime('%Y-%m-%d')
    return [
        # ユーザー選択メニューのブロック
        # # ユーザー選択
        # {
        #     "type": "section",
        #     "block_id": "user_select_block",
        #     "text": {"type": "mrkdwn", "text": "スケジュールを登録するユーザーを選択してください："},
        #     "accessory": {
        #         "type": "users_select",
        #         "placeholder": {"type": "plain_text", "text": "ユーザーを選択", "emoji": True},
        #         "action_id": "user_select_action"
        #     }
        # },
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


# # アイトルトコブロック
# def get_multi_schedule_blocks():
#     current_date = datetime.now().strftime('%Y-%m-%d')
#     return [
#         # ユーザー選択（複数人）
#         {
#             "type": "section",
#             "block_id": "multi_user_select_block",
#             "text": {"type": "mrkdwn", "text": "スケジュールを確認するユーザーを選択してください："},
#             "accessory": {
#                 "type": "multi_users_select",
#                 "placeholder": {"type": "plain_text", "text": "ユーザーを選択", "emoji": True},
#                 "action_id": "multi_user_select_action"
#             }
#         },
#         # 開始日付選択
#         {
#             "type": "input",
#             "block_id": "start_date_select_block",
#             "element": {
#                 "type": "datepicker",
#                 "initial_date": current_date,  # 今日の日付をデフォルト値として設定
#                 "action_id": "start_date_selected"
#             },
#             "label": {"type": "plain_text", "text": "開始日付を選択してください"}
#         },
#         # 終了日付選択
#         {
#             "type": "input",
#             "block_id": "end_date_select_block",
#             "element": {
#                 "type": "datepicker",
#                 "action_id": "end_date_selected"
#             },
#             "label": {"type": "plain_text", "text": "終了日付を選択してください（省略可）"}
#         },
#         # 「アイトルトコ」ボタン
#         {
#             "type": "actions",
#             "elements": [
#                 {
#                     "type": "button",
#                     "text": {"type": "plain_text", "text": "アイトルトコ"},
#                     "value": "find_schedule",
#                     "action_id": "find_schedule_button"
#                 }
#             ]
#         }
#     ]




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
            emp_code_url = get_empCode_url + f"&query=[{{\"items\":[{{\"field\":\"メールアドレス\",\"opr\":\"=\",\"value\":\"{email_prefix}\"}}]}}]"
            emp_code_response = requests.get(emp_code_url, headers={'X-API-Key': pe_api_key})
            emp_code_data = json.loads(emp_code_response.text)
            if emp_code_data["count"] > 0:
                emp_code = str(emp_code_data["records"][0]["社員番号"]["value"])
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


# スケジュール登録機能
@app.action("register_schedule_button")
def handle_register_schedule(ack, body, logger, client):
    ack()
    action_user_id = body["user"]["id"]
    values = body["view"]["state"]["values"]

    #  # ユーザー選択の存在チェック
    # user_selection = values["user_select_block"].get("user_select_action")
    # if user_selection:
    #     selected_user_id = user_selection.get("selected_user")
    #     emp_code = get_employee_code(client, selected_user_id, logger) if selected_user_id else None
    # else:
    #     emp_code = None

    # アクセスしたユーザーのメールアドレスから社員番号を取得
    emp_code = get_employee_code(client, action_user_id, logger)

    # 日付と件名の存在チェック
    date_selection = values["date_select_block"].get("date_selected")
    selected_date = date_selection.get("selected_date") if date_selection else None

    subject_input = values["subject_input_block"].get("subject_input")
    subject = subject_input.get("value") if subject_input else None

    # 必須項目のチェック
    if not emp_code or not selected_date or not subject:
        client.chat_postMessage(
            channel=action_user_id,
            text="未入力項目があります。"
        )
        return
    
    plan_class_id = values["plan_class_select_block"]["plan_class_selected"]["selected_option"]["value"]
    from_time = values["start_time_select_block"]["start_time_selected"]["selected_time"] or ""
    to_time = values["end_time_select_block"]["end_time_selected"]["selected_time"] or ""
    content = values["content_input_block"]["content_input"]["value"] or ""
    is_public = values["public_select_block"]["public_selected"]["selected_option"]["value"]
    
    if emp_code:
        # スケジュール登録APIへのリクエストを行う
        try:
            url = post_schedule_url
            headers = {
                "X-API-Key": pe_api_key,
                "Content-Type": "application/json"
            }
            data = {
                "corpId": corp_id,
                "empCode": emp_code,
                "fromDate": selected_date,
                "fromTime": from_time.replace(":", ""),
                "toTime": to_time.replace(":", ""),
                "schedulePlanClassId": plan_class_id,
                "subject": subject,
                "content": content,
                "isPublic": is_public,
            }
            response = requests.post(url, headers=headers, json=data)
            response_data = response.json()

            # ステータスコードのチェックを修正
            if response.status_code == 200 or "id" in response_data:
                client.chat_postMessage(
                    channel=action_user_id,
                    text=f"スケジュールを登録しました。ID: {response_data.get('id', '不明')}"
                )
            else:
                logger.error(f"Failed to register schedule: {response.text}")
                client.chat_postMessage(
                    channel=action_user_id,
                    text="スケジュール登録に失敗しました。"
                )
        except Exception as e:
            logger.error(f"Error while registering schedule: {e}")
            client.chat_postMessage(
                channel=action_user_id,
                text="スケジュール登録中にエラーが発生しました。"
            )
    else:
        client.chat_postMessage(
            channel=action_user_id,
            text="適切な社員番号が見つかりませんでした。"
        )


# # アイトルトココード
# @app.action("multi_user_select_action")
# def handle_multi_user_select_action(ack, body, logger):
#     ack()
#     logger.info(body)

# # 時間を分単位で扱う関数
# def time_to_minutes(t):
#     h, m = divmod(int(t), 100)
#     return h * 60 + m

# # 分を時間形式（HH:MM）に変換する関数
# def format_time(minutes):
#     return f"{minutes // 60:02d}:{minutes % 60:02d}"

# # 各ユーザーのスケジュールを取得
# def get_user_schedules(client, user_ids, start_date, end_date, logger):
#     schedules = {}
#     for user_id in user_ids:
#         emp_code = get_employee_code2(client, user_id, logger)
#         if emp_code:
#             user_schedule = get_power_egg_schedule2(emp_code, start_date, end_date, logger)
#             if user_schedule:
#                 schedules[user_id] = user_schedule
#     return schedules

# # ユーザー情報取得と社員番号の取得
# def get_employee_code2(client, user_id, logger):
#     user_info_response = client.users_info(user=user_id)
#     if user_info_response["ok"]:
#         user_email = user_info_response["user"]["profile"].get("email")
#         if user_email:
#             email_prefix = user_email.split('@')[0]
#             emp_code_url = f"http://192.168.254.101/pe4j/api/rest/v1/xdb/q/records.json?database=情報システム管理/全社共通IT/【極秘】E-mailアカウント管理&query=[{{\"items\":[{{\"field\":\"メールアドレス\",\"opr\":\"=\",\"value\":\"{email_prefix}\"}}]}}]"
#             emp_code_response = requests.get(emp_code_url, headers={'X-API-Key': pe_api_key})
#             emp_code_data = json.loads(emp_code_response.text)
#             if emp_code_data["count"] > 0:
#                 emp_code = str(emp_code_data["records"][0]["社員番号"]["value"])
#                 return "0" + emp_code if len(emp_code) == 5 else emp_code
#     logger.error(f"Failed to retrieve user info: {user_info_response.get('error', 'Unknown error')}")
#     return None

# # PowerEgg APIからスケジュールを取得
# def get_power_egg_schedule2(emp_code, start_date, end_date, logger):
#     url = "http://192.168.254.101/pe4j/api/rest/v1/schedule/schedules.json"
#     headers = {'X-API-Key': pe_api_key}
#     params = {
#         "corpId": "380050117",
#         "empCode": emp_code,
#         "fromDate": start_date,
#         "toDate": end_date,
#         "needParticipantName": 0,
#         "needResourceName": 0,
#         "includingNonParticipation": 0,
#     }
#     schedule_response = requests.get(url, headers=headers, params=params)
#     if schedule_response.ok:
#         data = schedule_response.json()
#         return [(s['fromTime'], s['toTime']) for s in data['schedules']]
#     logger.error("Failed to get schedule from PowerEgg API.")
#     return []

# # JSONデータから空いている時間帯を見つける関数
# def find_free_time_slots(schedules, start_time, end_time):
#     # 時間データが空でないか確認
#     occupied = [(time_to_minutes(s[0]), time_to_minutes(s[1])) for s in schedules if s[0] and s[1]]
#     occupied.sort()

#     free_slots = []
#     current = time_to_minutes(start_time)

#     for start, end in occupied:
#         if current < start:
#             free_slots.append((current, start))
#         current = max(current, end)

#     if current < time_to_minutes(end_time):
#         free_slots.append((current, time_to_minutes(end_time)))

#     return free_slots

# # # 複数人のスケジュールから共通の空き時間帯を見つける関数
# # def get_common_free_times(schedules_list):
# #     common_free_times = set(schedules_list[0])
# #     for slots in schedules_list[1:]:
# #         common_free_times = common_free_times.intersection(set(slots))
# #     return list(common_free_times)

# # 複数人の空いている時間から共通の空き時間を見つける関数
# def get_common_free_times(schedules_list):
#     # 全員のスケジュールを反転させて空き時間を計算
#     free_times_list = []
#     for schedules in schedules_list:
#         busy_times = [(time_to_minutes(start), time_to_minutes(end)) for start, end in schedules]
#         day_start = time_to_minutes('0000')
#         day_end = time_to_minutes('2359')
#         free_times = [(day_start, busy_times[0][0])] + \
#                      [(busy_times[i][1], busy_times[i+1][0]) for i in range(len(busy_times)-1)] + \
#                      [(busy_times[-1][1], day_end)]
#         free_times_list.append(free_times)

#     # 共通の空き時間を計算
#     common_free_times = set(free_times_list[0])
#     for free_times in free_times_list[1:]:
#         common_free_times = common_free_times.intersection(set(free_times))

#     return list(common_free_times)


# # 複数人の空き時間帯を確認するアクション
# @app.action("find_schedule_button")
# def handle_find_schedule(ack, body, logger, client):
#     ack()
#     action_user_id = body["user"]["id"]
#     values = body["view"]["state"]["values"]
#     selected_user_ids = values["multi_user_select_block"]["multi_user_select_action"]["selected_users"]
#     start_date = values["start_date_select_block"]["start_date_selected"]["selected_date"]
#     end_date = values["end_date_select_block"]["end_date_selected"]["selected_date"] or start_date

#     # 各ユーザーのスケジュールを取得
#     schedules = get_user_schedules(client, selected_user_ids, start_date, end_date, logger)

#     # 作業時間を設定（08:20〜17:20）
#     working_hours = ('0820', '1720')
    
#     # # 各ユーザーの空き時間を計算
#     # individual_free_slots = [find_free_time_slots(schedules[user_id], *working_hours) for user_id in selected_user_ids]

#     individual_free_slots = []
#     for user_id in selected_user_ids:
#         if user_id in schedules:
#             individual_free_slots.append(find_free_time_slots(schedules[user_id], *working_hours))
#         else:
#             logger.error(f"No schedule data found for user: {user_id}")

#     # 各ユーザーの空き時間帯をログに出力
#     logger.info(f"Individual free slots: {individual_free_slots}")

#     # 共通の空き時間を計算
#     common_free_times = get_common_free_times(individual_free_slots)

#     # 結果の整形と表示
#     if not common_free_times:
#         response_text = "共通の空き時間が見つかりませんでした。"
#     else:
#         formatted_common_free_times = [(format_time(start), format_time(end)) for start, end in common_free_times]
#         response_text = "共通の空き時間:\n" + "\n".join([f"{start} - {end}" for start, end in formatted_common_free_times])
    
#     client.chat_postMessage(channel=action_user_id, text=response_text)


# メイン部分
if __name__ == "__main__":
    SocketModeHandler(app, slack_app_token).start()