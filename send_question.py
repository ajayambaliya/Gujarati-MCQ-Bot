#!/usr/bin/env python3
"""
Telegram MCQ Bot - Send Random Gujarati Questions
Fetches from Google Apps Script and sends to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime
import pytz

# Telegram limits
TELEGRAM_MESSAGE_LIMIT = 4096
TELEGRAM_POLL_QUESTION_LIMIT = 300
TELEGRAM_POLL_OPTION_LIMIT = 100

# Configuration from environment variables
APPS_SCRIPT_URL = os.environ.get('APPS_SCRIPT_URL')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')


def check_ist_time_window():
    """Check if current time is within IST 11:00 AM - 10:00 PM"""
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    current_hour = now_ist.hour

    print(f"Current IST time: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    if 11 <= current_hour < 22:
        print("✓ Within allowed time window (11 AM - 10 PM IST)")
        return True
    else:
        print("✗ Outside allowed time window. Skipping execution.")
        return False


def fetch_random_question():
    """Fetch random question from Google Apps Script"""
    print("Fetching random question from Google Sheet...")

    try:
        response = requests.get(APPS_SCRIPT_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")

        question = data.get('data')
        print(f"✓ Fetched question ID: {question.get('id')}")
        return question

    except Exception as e:
        print(f"✗ Error fetching question: {e}")
        sys.exit(1)


def truncate_explanation(explanation, max_length):
    """Truncate explanation if too long"""
    if len(explanation) <= max_length:
        return explanation

    truncated = explanation[:max_length - 50]
    truncated += "\n\n... (શેષ ભાગ કાઢી નાખવામાં આવ્યો છે)"
    return truncated


def send_telegram_message(text, disable_web_preview=True):
    """Send text message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': disable_web_preview
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"✗ Error sending message: {e}")
        raise


def send_telegram_poll(question_text, options, correct_index):
    """Send poll to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPoll"

    question_text = question_text.strip()
    if len(question_text) > TELEGRAM_POLL_QUESTION_LIMIT:
        question_text = question_text[:TELEGRAM_POLL_QUESTION_LIMIT - 3] + "..."

    truncated_options = []
    for i, opt in enumerate(options):
        opt = opt.strip() if opt else f"Option {chr(65+i)}"
        if len(opt) > TELEGRAM_POLL_OPTION_LIMIT:
            opt = opt[:TELEGRAM_POLL_OPTION_LIMIT - 3] + "..."
        truncated_options.append(opt)

    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'question': question_text,
        'options': truncated_options,
        'type': 'quiz',
        'correct_option_id': correct_index
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def format_and_send_question(question):
    """
    POLL FIRST strategy
    """

    q_text = question['question']
    options = [
        question['option_a'],
        question['option_b'],
        question['option_c'],
        question['option_d']
    ]
    explanation = question['explanation']

    correct_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'a': 0, 'b': 1, 'c': 2, 'd': 3}
    correct_index = correct_map.get(question['correct'].strip(), 0)

    question_length = len(q_text)
    max_option_length = max(len(opt) for opt in options)

    # CASE 1: Direct poll
    if question_length <= TELEGRAM_POLL_QUESTION_LIMIT and max_option_length <= TELEGRAM_POLL_OPTION_LIMIT:
        send_telegram_poll(q_text, options, correct_index)

        if explanation:
            if len(explanation) > TELEGRAM_MESSAGE_LIMIT:
                explanation = truncate_explanation(explanation, TELEGRAM_MESSAGE_LIMIT)
            send_telegram_message(f"📘 <b>સમજૂતી:</b>\n{explanation}")

    # CASE 2: Hybrid mode
    else:
        if len(q_text) > TELEGRAM_MESSAGE_LIMIT:
            q_text = q_text[:TELEGRAM_MESSAGE_LIMIT - 50] + "\n\n... (પ્રશ્ન સંક્ષિપ્ત)"

        send_telegram_message(f"❓ <b>પ્રશ્ન:</b>\n{q_text}")

        truncated_options = [
            opt[:TELEGRAM_POLL_OPTION_LIMIT - 3] + "..." if len(opt) > TELEGRAM_POLL_OPTION_LIMIT else opt
            for opt in options
        ]

        send_telegram_poll("યોગ્ય વિકલ્પ પસંદ કરો:", truncated_options, correct_index)

        if explanation:
            if len(explanation) > TELEGRAM_MESSAGE_LIMIT:
                explanation = truncate_explanation(explanation, TELEGRAM_MESSAGE_LIMIT)
            send_telegram_message(f"📘 <b>સમજૂતી:</b>\n{explanation}")


def main():
    print("=" * 60)
    print("Telegram MCQ Bot - Random Question Sender")
    print("=" * 60)

    if not APPS_SCRIPT_URL or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("✗ Missing environment variables")
        sys.exit(1)

    if not check_ist_time_window():
        sys.exit(0)

    question = fetch_random_question()
    format_and_send_question(question)

    print("✓ Execution completed successfully")


if __name__ == "__main__":
    main()
