import requests
from datetime import datetime

def send_report_to_slack(sent_contents):
    slack_token = "トークン"
    success_results = []  # 各レポートの処理結果を辞書形式で格納

    try:
        for report in sent_contents:  # リスト内の各辞書を処理
            try:
                made_success = report.get('success')
                trouble_contents = report.get('trouble_contents')
                assign = report.get('assign')
                property_name = report.get('property_name', '')

                if made_success == "ok":
                    # 1) メインメッセージをSlackへ送信
                    message_payload = create_message_payload(report, trouble_contents, assign, property_name)
                    main_message_response = send_to_slack(slack_token, message_payload)

                    # 2) メインメッセージの thread_ts を取得
                    thread_ts = main_message_response.get('ts')

                    # 3) 無効化（deactivate）用のメッセージを作成＆送信
                    deactivate_payload = create_necessity_payload(report, thread_ts)
                    send_to_slack(slack_token, deactivate_payload)

                    # 4) 特定のトラブル内容ならリプライを送る
                    if trouble_contents == "アメニティ・リネン・消耗品不備":
                        reply_payload = create_reply_payload(report, thread_ts, property_name)
                        send_to_slack(slack_token, reply_payload)

                elif made_success == "error":
                    error_payload = create_error_payload(report)
                    send_to_slack(slack_token, error_payload)

                success_results.append({"success": made_success})

            except Exception as e:
                print(f"Error processing report: {e}")
                success_results.append({"success": "error"})
                continue

    except Exception as e:
        print(f"Global error: {e}")
        success_results.append({"success": "error"})

    return success_results





def create_message_payload(report, trouble_contents, assign, property_name):
    stay_period = f"{format_date(report.get('stay_start'))}~{format_date(report.get('stay_end'))}"
    created_at = convert_iso_to_custom_format(report.get('created_at'))
    color = (
        "#ED1A3D" if trouble_contents in ["自火報トラブル", "物理鍵トラブル", "TTlockトラブル"]
        else "#f2c744" if assign == "CX"
        else "#00FF00" if assign == "設備機器"
        else "#FFA500" if assign == "startup"
        else "#0000ff"  
    )

    user1 = "<!subteam^S07PPNZCB6V>" #cs-tokyo
    user2 = "<!subteam^S05NVPXMSNP>" #task
    user3 = "<!subteam^S07LRFPBQH2>" #設備機器
    user4 = "<!subteam^SFDUBF1CM>" #SU
    

    return {
        "channel": "C07AHJ1T17E",  # Replace with the actual channel ID or name
        "text": user1 if assign == "CX"  else user3 if assign == "設備機器" else user4 if assign== "startup" else user2,
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "❗️トラブル報告❗️", "emoji": True}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*物件名:*\n{property_name}"},
                            {"type": "mrkdwn", "text": f"*契約属性:*\n{report.get('contract_type')}"},
                            {"type": "mrkdwn", "text": f"*分類:*\n{trouble_contents}"},
                            {"type": "mrkdwn", "text": f"*フォームID:*\n{report.get('Submission ID')}"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*誰から（予約コード）:*\n{report.get('rq_person')}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*何が起きた:*\n{report.get('incident')}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*何をして欲しい:*\n{report.get('request')}"}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*予約経路:*\n{report.get('route')}"},
                            {"type": "mrkdwn", "text": f"*滞在期間:*\n{stay_period}"},
                            {"type": "mrkdwn", "text": f"*入力日時:*\n{created_at}"},
                            {"type": "mrkdwn", "text": f"*入力者:*\n{report.get('input_by')}"},
                            {"type": "mrkdwn", "text": f"*トラブルURL:*\n{report.get('trouble_url')}"},
                            {"type": "mrkdwn", "text": f"*引き継ぎフォームID:*\n{report.get('handover_id')}"},
                            {"type": "mrkdwn", "text": f"*m2m_管理者画面URL:*\n{report.get('admin_url')}"},
                            {"type": "mrkdwn", "text": f"*m2m_cleaner画面URL:*\n{report.get('cleaner_url')}"}
                        ]
                    }
                ]
            }
        ]
    }

def create_reply_payload(report,thread_ts, property_name):
    return {
        "channel": "C07AHJ1T17E",  # Replace with the actual channel ID or name
        "text": f"{property_name}の食器用洗剤の不足であれば、次回清掃時に食器用洗剤のピッキングが必要です。以下のボタンから選択してください。\n ※東京の物件のみ",
        "thread_ts": thread_ts,
        "attachments": [
            {
                "blocks": [
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "必要", "emoji": True},
                                "style": "primary",
                                "value": "必要",
                                "action_id": "button_approve"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "不要", "emoji": True},
                                "style": "danger",
                                "value": "不要",
                                "action_id": "button_reject"
                            },
                                              {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*誰から（予約コード）:*\n{report.get('rq_person')}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*何が起きた:*\n{report.get('incident')}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*何をして欲しい:*\n{report.get('request')}"}
                    }
                        ]
                    }
                ]
            }
        ]
    }

def create_necessity_payload(report, thread_ts):
    response = report.get("response") or ""


    print(f"response: {response}")

    return {
        "channel": "C07AHJ1T17E",
        "text": "対応が必要ですか？（不要ボタンを押した場合ツアーが無効化されます）",
        "thread_ts": thread_ts,
        "attachments": [
            {
                "blocks": [
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "必要", "emoji": True},
                                "style": "primary",
                                "action_id": "button_need"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "不要", "emoji": True},
                                "style": "danger",
                                "value": response,
                                "action_id": "button_disable"
                            }
                        ]
                    }
                ]
            }
        ]
    }





def create_error_payload(report):
    stay_period = f"{format_date(report.get('stay_start'))}~{format_date(report.get('stay_end'))}"
    created_at = convert_iso_to_custom_format(report.get('created_at'))

    return {
        "channel": "C07AHJ1T17E",  # Replace with the actual channel ID or name
        "attachments": [
            {
                "color": "#000000",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "☠️ツアー作成失敗☠️", "emoji": True}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*物件名:*\n{report.get('property_name')}"},
                            {"type": "mrkdwn", "text": f"*契約属性:*\n{report.get('contract_type')}"},
                            {"type": "mrkdwn", "text": f"*分類:*\n{report.get('trouble_contents')}"},
                            {"type": "mrkdwn", "text": f"*フォームID:*\n{report.get('Submission ID')}"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*誰から（予約コード）:*\n{report.get('rq_person')}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*何が起きた:*\n{report.get('incident')}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*何をして欲しい:*\n{report.get('request')}"}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*予約経路:*\n{report.get('route')}"},
                            {"type": "mrkdwn", "text": f"*滞在期間:*\n{stay_period}"},
                            {"type": "mrkdwn", "text": f"*入力日時:*\n{created_at}"},
                            {"type": "mrkdwn", "text": f"*入力者:*\n{report.get('input_by')}"},
                            {"type": "mrkdwn", "text": f"*トラブルURL:*\n{report.get('trouble_url')}"},
                            {"type": "mrkdwn", "text": f"*引き継ぎフォームID:*\n{report.get('handover_id')}"},
                            {"type": "mrkdwn", "text": f"*m2m_管理者画面URL:*\n{report.get('admin_url')}"},
                            {"type": "mrkdwn", "text": f"*m2m_cleaner画面URL:*\n{report.get('cleaner_url')}"}
                        ]
                    }
                ]
            }
        ]
    }


def send_to_slack(token, payload):
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()

    # レスポンスデータをログに出力
    print(f"Slack API Response: {response_data}")

    if not response_data.get("ok"):
        print(f"Slack API Error: {response_data.get('error')} - Payload: {payload}")
        raise Exception(f"Slack API Error: {response_data.get('error')}")


    if not response_data.get("ok"):
        print(f"Slack API Error: {response_data.get('error')} - Payload: {payload}")
        raise Exception(f"Slack API Error: {response_data.get('error')}")

    return response_data

def format_date(date):
    if not date:
        return "N/A"  # 値が存在しない場合のデフォルト値
    if isinstance(date, str):
        return date
    try:
        return date.strftime('%Y-%m-%d')
    except AttributeError:
        return "N/A"  # None やその他の無効値を処理


def convert_iso_to_custom_format(iso_string):
    if not iso_string:
        return "N/A"  # 値が存在しない場合のデフォルト値
    try:
        # ISO 8601フォーマットの場合
        date = datetime.fromisoformat(iso_string)
    except ValueError:
        try:
            # "YYYY-MM-DD HH:MM:SS" フォーマットの場合
            date = datetime.strptime(iso_string, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return "N/A"  # 解析できない場合のデフォルト値
    return date.strftime('%Y/%m/%d %H:%M:%S')
