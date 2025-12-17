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
    
    if 11 <= current_hour < 22:  # 11 AM to 10 PM (22:00)
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


def is_numbered_question(text):
    """Check if question contains numbered statements"""
    patterns = [
        r'\n\s*\d+\.',  # 1. 2. 3.
        r'\n\s*\(\d+\)',  # (1) (2) (3)
        r'\n\s*[ivxIVX]+\.',  # i. ii. iii. or I. II. III.
        r'\n\s*[a-zA-Z]\.',  # a. b. c.
    ]
    
    import re
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def format_question_text(question_text):
    """Format question text, preserving numbered structure"""
    # Already formatted in the sheet, just return as is
    # The formatting should be done when creating the Excel file
    return question_text.strip()


def truncate_explanation(explanation, max_length):
    """Truncate explanation if too long"""
    if len(explanation) <= max_length:
        return explanation
    
    # Truncate and add indicator
    truncated = explanation[:max_length - 50]  # Leave room for indicator
    truncated += "\n\n... (શેષ ભાગ કાઢી નાખવામાં આવ્યો છે)"
    return truncated


def send_telegram_message(text):
    """Send text message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': text,
        'parse_mode': 'HTML'
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
    
    # Truncate question if needed
    if len(question_text) > TELEGRAM_POLL_QUESTION_LIMIT:
        question_text = question_text[:TELEGRAM_POLL_QUESTION_LIMIT - 3] + "..."
    
    # Truncate options if needed
    truncated_options = []
    for opt in options:
        if len(opt) > TELEGRAM_POLL_OPTION_LIMIT:
            opt = opt[:TELEGRAM_POLL_OPTION_LIMIT - 3] + "..."
        truncated_options.append(opt)
    
    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'question': question_text,
        'options': truncated_options,
        'type': 'quiz',
        'correct_option_id': correct_index,
        'is_anonymous': False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"✗ Error sending poll: {e}")
        raise


def format_and_send_question(question):
    """Format and send question based on length"""
    
    q_text = question['question']
    opt_a = question['option_a']
    opt_b = question['option_b']
    opt_c = question['option_c']
    opt_d = question['option_d']
    correct = question['correct']
    explanation = question['explanation']
    
    # Map correct answer to index
    correct_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    correct_index = correct_map.get(correct.upper(), 0)
    
    # Build full message
    full_message = f"❓ <b>પ્રશ્ન:</b>\n{q_text}\n\n"
    full_message += f"A️⃣ {opt_a}\n"
    full_message += f"B️⃣ {opt_b}\n"
    full_message += f"C️⃣ {opt_c}\n"
    full_message += f"D️⃣ {opt_d}\n\n"
    full_message += f"✅ <b>સાચો જવાબ:</b> {correct}\n\n"
    
    if explanation:
        # Truncate explanation if needed
        max_explanation_length = TELEGRAM_MESSAGE_LIMIT - len(full_message) - 100
        if len(explanation) > max_explanation_length:
            explanation = truncate_explanation(explanation, max_explanation_length)
        full_message += f"📘 <b>સમજૂતી:</b>\n{explanation}"
    
    # Check if full message fits
    if len(full_message) <= TELEGRAM_MESSAGE_LIMIT:
        # Send as single message
        print("Sending as single message...")
        send_telegram_message(full_message)
        print("✓ Message sent successfully")
    else:
        # Split: Question as message, Options as poll
        print("Message too long. Splitting into message + poll...")
        
        # Send question text
        question_message = f"❓ <b>પ્રશ્ન:</b>\n{q_text}"
        if explanation:
            max_exp_len = TELEGRAM_MESSAGE_LIMIT - len(question_message) - 100
            if len(explanation) > max_exp_len:
                explanation = truncate_explanation(explanation, max_exp_len)
            question_message += f"\n\n📘 <b>સમજૂતી:</b>\n{explanation}"
        
        send_telegram_message(question_message)
        print("✓ Question text sent")
        
        # Send poll with options
        poll_question = "વિકલ્પો પસંદ કરો:"
        options = [opt_a, opt_b, opt_c, opt_d]
        send_telegram_poll(poll_question, options, correct_index)
        print("✓ Poll sent")


def main():
    """Main execution"""
    print("=" * 60)
    print("Telegram MCQ Bot - Random Question Sender")
    print("=" * 60)
    print()
    
    # Validate environment variables
    if not APPS_SCRIPT_URL:
        print("✗ Error: APPS_SCRIPT_URL not set")
        sys.exit(1)
    
    if not TELEGRAM_BOT_TOKEN:
        print("✗ Error: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    
    if not TELEGRAM_CHANNEL_ID:
        print("✗ Error: TELEGRAM_CHANNEL_ID not set")
        sys.exit(1)
    
    # Check time window
    if not check_ist_time_window():
        print("Exiting without sending message.")
        sys.exit(0)
    
    print()
    
    # Fetch question
    question = fetch_random_question()
    
    print()
    print("Question details:")
    print(f"  ID: {question['id']}")
    print(f"  Question length: {len(question['question'])} chars")
    print(f"  Correct answer: {question['correct']}")
    print()
    
    # Send to Telegram
    format_and_send_question(question)
    
    print()
    print("=" * 60)
    print("✓ Execution completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
