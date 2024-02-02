import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
import json


# 設定ファイルの読み込み
with open("config2.json", encoding="utf-8") as config_file:
    config = json.load(config_file)

SLACK_APP_TOKEN = config["slack_app_token"]
SLACK_BOT_TOKEN = config["slack_bot_token"]
OPENAI_API_KEY = config["OPENAI_API_KEY"]
CHANNEL_ID = config["channel_id"]
admin_user = config["admin_user"]

# Slack Bolt アプリの初期化（Socket Modeで）
app = App(token=SLACK_BOT_TOKEN)

clientai = OpenAI(api_key=OPENAI_API_KEY)


def log_to_json(department, user_id, user_name, content, response_content, parent_ts, message_ts):
    log_data = {
        "department": department,
        "user_id": user_id,
        "user_name": user_name,
        "content": content,
        "response_content": response_content,
        "parent_ts": parent_ts,  # 返信の親メッセージのTS
        "message_ts": message_ts,  # 返信自体のTS
    }

    with open('log_file.json', 'a', encoding="utf-8") as log_file:
        json.dump(log_data, log_file, ensure_ascii=False)
        log_file.write('\n')  # 次のログエントリのための改行


# 「戻る」ボタンブロック
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

# 最初のホームページを表示する関数
def publish_initial_home_view(client, user_id, logger):
    try:
        # Home Tabに表示する内容を定義
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "⚠公序良俗に反した投稿はしないでください！\n⚠個人情報は入力しないでください！"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "※所属部署の情報は統計分析に使わせていただきます。"
                        }
                    },
                    {
		            	"type": "divider"
		            },
                    {
                        "type": "section",
                        "block_id": "department_select_block",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*所属部門を選択してください*"
                        },
                        "accessory": {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "部門を選択"
                            },
                            "options": [
                                {
                                    "text": {"type": "plain_text", "text": "陶磁器事業部"},
                                    "value": "ceramics"
                                },
                                {
                                    "text": {"type": "plain_text", "text": "水創り事業部"},
                                    "value": "water_creation"
                                },
                                {
                                    "text": {"type": "plain_text", "text": "環境プラント事業部"},
                                    "value": "environmental_plant"
                                },
                                {
                                    "text": {"type": "plain_text", "text": "バンクチュール事業部"},
                                    "value": "baincture"
                                },
                                {
                                    "text": {"type": "plain_text", "text": "機能セラミック事業部"},
                                    "value": "functional_ceramics"
                                },
                                {
                                    "text": {"type": "plain_text", "text": "その他本社部門"},
                                    "value": "other_headquarters"
                                }
                            ],
                            "initial_option": {"text": {"type": "plain_text", "text": "陶磁器事業部"}, "value": "ceramics"},
                            "action_id": "department_select"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "input_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "input_message",
                            "multiline": True
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "▼こちらにあなたのお悩みを聞かせてね！▼"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "投稿！"
                                },
                                "value": "submit_value",
                                "action_id": "submit_button"
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
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "管理者ボタン！"
                                },
                                "value": "admin_value",
                                "action_id": "admin_button"
                            }
                        ]
                    },
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error publishing initial home view: {e}")

# 「戻る」ボタンアクション定義
@app.action("back_button")
def handle_back_button(ack, body, client, logger):
    ack()
    publish_initial_home_view(client, body["user"]["id"],logger)


@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    try:
        user_id = event["user"]
        publish_initial_home_view(client, user_id, logger)
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


# ボタンが押されたときの処理
@app.action("submit_button")
def handle_submission(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    # ユーザー情報を取得
    user_info = client.users_info(user=user_id)
    user_name = user_info["user"]["name"] if user_info["ok"] else "unknown"
    user_input = body["view"]["state"]["values"]["input_block"]["input_message"]["value"]
    selected_department = body["view"]["state"]["values"]["department_select_block"]["department_select"]["selected_option"]["value"]

    # 「投稿ありがとうございました」のメッセージを表示する新しいビューを定義
    thank_you_view = {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "投稿ありがとうございました。回答はチャンネルに投稿されます！"
                    }
                },
                get_back_button_block()
            ]
        }

        # Home Tabを更新して新しいビューを表示
    client.views_publish(
            user_id=user_id,
            view=thank_you_view
        )
    try:
        # 入力されたテキストを取得
        user_input = body["view"]["state"]["values"]["input_block"]["input_message"]["value"]

        # OpenAI APIにリクエストを送信して回答を得る
        response = clientai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ]
        )

        # 特定のチャンネルに質問を投稿
        channel_id = CHANNEL_ID
        question_attachment = [
            {
                "color": "#e0e0e0",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "💌*RN: 恋するうさぎちゃんからのおたより！*\n```" + user_input + "```"
                        }
                    }
                ]
            }
        ]
        result = client.chat_postMessage(
            channel=channel_id,
            attachments=question_attachment,
            text="AIから返信があるよ！",
        )
        question_ts = result["ts"]

        # スレッドにAIの回答を投稿
        response_attachment = [
            {
                "color": "#E32D91",
                "blocks": [
                    {
                            "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*わたしのアイディアは下の通りだよ！*\n" + response.choices[0].message.content
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "❤リスナーのみんなも答えてみてね！",
                        }
                    }
                ]
            }
        ]
        app_response = client.chat_postMessage(
            channel=channel_id,
            thread_ts=result["ts"],
            attachments=response_attachment,
            text="❤リスナーのみんなも答えてみてね！",
        )
        client.chat_postMessage(channel=user_id, text="*あなたのおなやみ*\n```" + user_input + "```\n" + "*わたしのアイディアは下の通りだよ！*\n" + response.choices[0].message.content)

        response_ts = app_response["ts"]

        # ログを保存
        log_to_json(selected_department, user_id, user_name, user_input, response.choices[0].message.content, question_ts, response_ts)

    except Exception as e:
        logger.error(f"Error handling submission: {e}")
        client.chat_postMessage(channel=user_id, text="ごめんねエラーが発生したよ。入力テキストを見直してもう一度試してみてね！")


@app.action("department_select")
def handle_department_select(ack, body, logger):
    ack()
    # 選択された部門の取得
    selected_department = body["actions"][0]["selected_option"]["value"]
    logger.info(f"Selected department: {selected_department}")

    # 必要に応じて追加の処理をここに実装
    # 例: 選択された部門に基づいて特定の情報をユーザーに表示する


@app.action("admin_button")
def admin_app(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]

    if user_id not in admin_user:
        # アプリホームにメッセージを表示するビューを更新
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "残念ですが、管理者以外はアクセスできません。"
                        }
                    },
                    get_back_button_block()
                ]
            }
        )
        return
    else:
        publish_admin_home_view(client, user_id)


# 管理者用のホーム画面を表示する関数
def publish_admin_home_view(client, user_id):
    client.views_publish(
        user_id=user_id,
        view={
            "type": "home",
            "blocks": [
                {
                    "type": "input",
                    "block_id": "link_input_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "link_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "メッセージのリンクを入力してください"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "メッセージリンク"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "削除"
                            },
                            "style": "danger",
                            "value": "delete_message",
                            "action_id": "delete_button"
                        }
                    ]
                },
                get_back_button_block()
            ]
        }
    )

@app.action("delete_button")
def handle_delete_button(ack, body, client, logger):
    ack()
    user_id = body["user"]["id"]
    link_input = body["view"]["state"]["values"]["link_input_block"]["link_input"]["value"]

    # リンクからチャンネルIDとメッセージのタイムスタンプを抽出
    channel_id, message_ts = extract_info_from_link(link_input)

    # メッセージを削除
    try:
        client.chat_delete(channel=channel_id, ts=message_ts)
        # 成功メッセージをユーザーに表示
        client.chat_postMessage(channel=user_id, text="メッセージを削除しました。")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        # エラーメッセージをユーザーに表示
        client.chat_postMessage(channel=user_id, text="メッセージの削除に失敗しました。")

def extract_info_from_link(link):
    parts = link.split('/')
    channel_id = parts[-2]
    message_ts = parts[-1].split('?')[0].replace('p', '.')
    return channel_id, message_ts


# リアクションが追加されたイベントを捕捉するリスナー
@app.event("reaction_added")
def handle_reaction_added(event, client, logger):
    # チャンネルIDを取得
    channel_id = event["item"]["channel"]
    # 特定のチャンネルに限定
    if channel_id == CHANNEL_ID:
        # メッセージのTS（タイムスタンプ）を取得
        message_ts = event["item"]["ts"]
        # リアクションを追加したユーザーのIDを取得
        user_id = event["user"]
        
        # ユーザー名の取得
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["name"] if user_info["ok"] else "unknown"

        # ログデータに追加
        log_reaction_to_json(channel_id, message_ts, user_id, user_name)


def log_reaction_to_json(channel_id, message_ts, user_id, user_name):
    log_data = {
        "channel_id": channel_id,
        "message_ts": message_ts,
        "user_id": user_id,
        "user_name": user_name,
        "action": "reaction_added"
    }

    with open('reaction_log_file.json', 'a', encoding="utf-8") as log_file:
        json.dump(log_data, log_file, ensure_ascii=False)
        log_file.write('\n')  # 次のログエントリのための改行


@app.event("message")
def handle_message(event, client, logger):
    # チャンネルIDとイベントが返信であるかどうかを確認
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")
    message_ts = event.get("ts")

    # 特定のチャンネルに限定し、返信のみを対象とする
    if channel_id == CHANNEL_ID and thread_ts and thread_ts != message_ts:
        user_id = event.get("user")
        
        # ユーザー名を取得
        result = client.users_info(user=user_id)
        user_info = result.data
        user_name = user_info["user"]["name"] if "user" in user_info else "unknown"

        # ログに記録
        log_to_json(None, user_id, user_name, None, event.get("text"), thread_ts, message_ts)


# Socket Modeハンドラの起動
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

