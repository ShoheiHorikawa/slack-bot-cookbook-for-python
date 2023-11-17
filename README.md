# slack-bot-cookbook
Slack bot作成用リポジトリ

# Slack Setting Sample
## Create New App
- From Scratch
- App Name: Favorite Name
- Pick a work space to develop your app in: Your Workspace  

    
## OAuth & Permissions
Bot Token Scopes
- chat:write
- users:read
- users:read.email


## Socket Mode
- Enable Socket Mode: On
- Event Subscription: On
    - Event name: app_home_opened


## App Home
- Show Tab
- Home Tab: On


# Prepare
## Python
- version: 3.9.9 (Favorite Version)

## Package
```
pip install -r requirements.txt
```

## Token, API_key
### それぞれ[sample](sample/)内にサンプルファイルがあるので、各自のキーで上書きして、スクリプトと同じディレクトリに保存してください。  
### なお、スクリプトによって必要なファイルは異なるので、下記の[Codes](#codes)を参照ください。
- slack_bot_token.txt   :Slackのbotのtoken
- slack_app_token.txt   :Slackのappのtoken
- pe_api_key.txt        :POWER EGGのAPIキー  
- config.json           :PE_slack_connection.py用設定ファイル


# Codes
## [001_hometab_test.py](001_hometab_test.py)
### 概要
Slack botのホーム画面あれこれのキホン。  
Blockをいろいろ試しています。

### 必要な設定ファイル
- slack_app_token.py
- slack_bot_token.py


## [002_structure_test.py](002_structure_test.py)
### 概要
Slack botのBlockを入れ子にしてみるテスト。

### 必要な設定ファイル
- slack_app_token.py
- slack_bot_token.py


## [100_pe_sche.py](100_pe_sche.py)
### 概要
SlackとPOWER EGGをAPI経由で接続するスクリプト。  
名前は「PE_Sche | ぺぇすけ」です。  
以下の機能が実装されています。  
- スケジュールの確認（単一ユーザー）
- スケジュールの確認（複数ユーザー）
- スケジュール登録(自分のみ)  

`empCode`（社員番号）を取ってくる方法は環境により様々です。  
本スクリプトでは以下の手順で`empCode`を取得しています。
1. Slack Botがユーザーの登録メールアドレスを取得。
2. アドレスとPOWER EGGのWEB データベース(社員マスタなど)と突き合わせ、該当する社員番号を取得。  

そのため、データベースと社員番号が紐づいていないユーザーはスケジュールの確認と登録ができません。

### アプリアイコン
<img src="icon/Icon_PE_Sche.png" width="160px">  

*created by DALL-E3*


### 必要な設定ファイル
- config.json