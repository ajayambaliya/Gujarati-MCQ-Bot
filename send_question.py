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
    """
    Format and send question - POLL FIRST approach
    
    Decision flow:
    1. Try to send as POLL (if question ≤ 300 chars and all options ≤ 100 chars)
    2. If poll not possible, send question text + poll with short question
    3. Always send explanation separately (if exists)
    """
    
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
    
    # Prepare options list
    options = [opt_a, opt_b, opt_c, opt_d]
    
    # Check lengths
    question_length = len(q_text)
    option_lengths = [len(opt) for opt in options]
    max_option_length = max(option_lengths)
    
    print(f"Question length: {question_length} chars")
    print(f"Max option length: {max_option_length} chars")
    
    # CASE 1: Question ≤ 300 AND all options ≤ 100 → SEND AS POLL
    if question_length <= TELEGRAM_POLL_QUESTION_LIMIT and max_option_length <= TELEGRAM_POLL_OPTION_LIMIT:
        print("✓ Sending as POLL (question + options fit)")
        
        # Send poll with question as poll question
        send_telegram_poll(q_text, options, correct_index)
        print("✓ Poll sent")
        
        # Send explanation separately if exists
        if explanation:
            if len(explanation) > TELEGRAM_MESSAGE_LIMIT:
                explanation = truncate_explanation(explanation, TELEGRAM_MESSAGE_LIMIT)
            
            explanation_message = f"📘 <b>સમજૂતી:</b>\n{explanation}"
            send_telegram_message(explanation_message)
            print("✓ Explanation sent")
    
    # CASE 2: Question > 300 OR any option > 100 → HYBRID MODE
    else:
        print("⚠ Question or options too long for direct poll")
        print("→ Using hybrid mode: question text + poll")
        
        # Truncate question if > 4096
        if question_length > TELEGRAM_MESSAGE_LIMIT:
            q_text = q_text[:TELEGRAM_MESSAGE_LIMIT - 50]
            q_text += "\n\n... (પ્રશ્ન સંક્ષિપ્ત કરવામાં આવ્યો છે)"
        
        # Send question text only
        question_message = f"❓ <b>પ્રશ્ન:</b>\n{q_text}"
        send_telegram_message(question_message)
        print("✓ Question text sent")
        
        # Truncate options if needed
        truncated_options = []
        for opt in options:
            if len(opt) > TELEGRAM_POLL_OPTION_LIMIT:
                opt = opt[:TELEGRAM_POLL_OPTION_LIMIT - 3] + "..."
            truncated_options.append(opt)
        
        # Send poll with short question
        poll_question = "યોગ્ય વિકલ્પ પસંદ કરો:"
        send_telegram_poll(poll_question, truncated_options, correct_index)
        print("✓ Poll sent")
        
        # Send explanation if exists
        if explanation:
            if len(explanation) > TELEGRAM_MESSAGE_LIMIT:
                explanation = truncate_explanation(explanation, TELEGRAM_MESSAGE_LIMIT)
            
            explanation_message = f"📘 <b>સમજૂતી:</b>\n{explanation}"
            send_telegram_message(explanation_message)
            print("✓ Explanation sent")


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
