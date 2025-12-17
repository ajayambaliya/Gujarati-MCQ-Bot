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


def fetch_random_quote():
    """Fetch a random motivational quote from GitHub Gist"""
    try:
        url = "https://gist.githubusercontent.com/nasrulhazim/54b659e43b1035215cd0ba1d4577ee80/raw/e3c6895ce42069f0ee7e991229064f167fe8ccdc/quotes.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        quotes = data.get('quotes', [])
        
        if not quotes:
            return None
        
        # Try to find a short quote (≤ 150 chars)
        import random
        random.shuffle(quotes)
        
        for quote_obj in quotes:
            quote_text = quote_obj.get('quote', '')
            if quote_text and len(quote_text) <= 150:
                return quote_text
        
        # If no short quote found, return first one truncated
        first_quote = quotes[0].get('quote', '')
        if len(first_quote) > 150:
            first_quote = first_quote[:147] + "..."
        return first_quote
    
    except Exception as e:
        print(f"⚠ Failed to fetch quote: {e}")
        return None


def send_promotional_message():
    """Send promotional message about the channel with motivational quote"""
    
    # Fetch random quote
    quote = fetch_random_quote()
    
    # Build compact promotional message
    promo_message = """📚 <b>Current Adda</b>
🎯 <b>ગુજરાત સરકારી નોકરી તૈયારી</b>

✅ દરરોજ MCQ પ્રશ્નો
✅ ગુજરાતી કરંટ અફેર્સ

🔔 <b>જોઈન કરો:</b> https://t.me/currentadda"""
    
    # Add quote if available
    if quote:
        promo_message += f'\n\n💡 <i>"{quote}"</i>'
    
    promo_message += "\n\n<i>#GPSC #GSSSB #Talati #CurrentAffairs</i>"
    
    try:
        send_telegram_message(promo_message, disable_web_preview=True)
        print("✓ Promotional message sent")
        if quote:
            print(f"  Quote: {quote[:50]}...")
    except Exception as e:
        print(f"⚠ Failed to send promotional message: {e}")
        # Don't fail the whole process if promo fails


def send_telegram_poll(question_text, options, correct_index):
    """Send poll to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPoll"
    
    # Validate question text
    if not question_text or not question_text.strip():
        raise ValueError("Poll question cannot be empty")
    
    question_text = question_text.strip()
    
    # Truncate question if needed
    if len(question_text) > TELEGRAM_POLL_QUESTION_LIMIT:
        question_text = question_text[:TELEGRAM_POLL_QUESTION_LIMIT - 3] + "..."
    
    # Truncate options if needed and validate
    truncated_options = []
    for i, opt in enumerate(options):
        # Ensure option is not empty
        if not opt or not opt.strip():
            opt = f"Option {chr(65+i)}"  # A, B, C, D
        
        opt = opt.strip()
        
        if len(opt) > TELEGRAM_POLL_OPTION_LIMIT:
            opt = opt[:TELEGRAM_POLL_OPTION_LIMIT - 3] + "..."
        
        truncated_options.append(opt)
    
    # Validate: Must have at least 2 options
    if len(truncated_options) < 2:
        raise ValueError("Poll must have at least 2 options")
    
    # Validate: correct_index must be valid
    if correct_index < 0 or correct_index >= len(truncated_options):
        raise ValueError(f"Invalid correct_index: {correct_index} (must be 0-{len(truncated_options)-1})")
    
    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'question': question_text,
        'options': truncated_options,
        'type': 'quiz',
        'correct_option_id': correct_index
        # Note: is_anonymous is not supported for channel chats
    }
    
    try:
        print(f"Sending poll with payload:")
        print(f"  Question: {question_text[:50]}...")
        print(f"  Options: {len(truncated_options)} options")
        print(f"  Correct index: {correct_index}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"✗ Telegram API Error Response:")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"✗ Error sending poll: {e}")
        print(f"  Payload was: {payload}")
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
    
    # Map correct answer to index (handle both uppercase and lowercase)
    correct_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'a': 0, 'b': 1, 'c': 2, 'd': 3}
    correct_index = correct_map.get(correct.strip(), 0)
    
    print(f"Correct answer: '{correct}' → Index: {correct_index}")
    
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
        
        # Send promotional message
        print()
        send_promotional_message()
    
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
        
        # Send promotional message
        print()
        send_promotional_message()


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
