# 🤖 Telegram MCQ Bot Setup Guide

Complete setup guide for automated Gujarati MCQ questions on Telegram.

---

## 📋 Prerequisites

1. Google Account with Google Sheets access
2. Telegram account
3. GitHub account

---

## 🔧 Step-by-Step Setup

### Step 1: Prepare Google Sheet

1. **Upload your Excel file** to Google Sheets:
   - Go to https://sheets.google.com
   - Click "File" → "Import" → Upload `mcq-questions.xlsx`
   - Or create new sheet and paste data

2. **Verify columns** (must be in this order):
   ```
   id | question | option_a | option_b | option_c | option_d | correct | explanation
   ```

3. **Keep the sheet PRIVATE** (do not share publicly)

---

### Step 2: Deploy Google Apps Script

1. **Open Script Editor**:
   - In your Google Sheet, click "Extensions" → "Apps Script"

2. **Paste the code**:
   - Delete any existing code
   - Copy entire content from `telegram-bot/apps-script.js`
   - Paste into the editor

3. **Save the project**:
   - Click the disk icon or Ctrl+S
   - Name it: "MCQ Random Question API"

4. **Deploy as Web App**:
   - Click "Deploy" → "New deployment"
   - Click gear icon ⚙️ → Select "Web app"
   - Configure:
     - **Description**: "Random Question API"
     - **Execute as**: Me (your email)
     - **Who has access**: Anyone
   - Click "Deploy"
   - **Authorize** the app (click "Authorize access")
   - Select your Google account
   - Click "Advanced" → "Go to [Project Name] (unsafe)"
   - Click "Allow"

5. **Copy the Web App URL**:
   - After deployment, you'll see a URL like:
     ```
     https://script.google.com/macros/s/AKfycbx.../exec
     ```
   - **SAVE THIS URL** - you'll need it later

6. **Test the API**:
   - Open the URL in your browser
   - You should see JSON response with a random question
   - Example:
     ```json
     {
       "success": true,
       "data": {
         "id": "123",
         "question": "પ્રશ્ન...",
         "option_a": "વિકલ્પ A",
         ...
       }
     }
     ```

---

### Step 3: Create Telegram Bot

1. **Open Telegram** and search for `@BotFather`

2. **Create new bot**:
   - Send: `/newbot`
   - Enter bot name: `Gujarati MCQ Bot`
   - Enter username: `gujarati_mcq_bot` (must end with 'bot')

3. **Save the Bot Token**:
   - BotFather will give you a token like:
     ```
     1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
     ```
   - **SAVE THIS TOKEN** securely

4. **Create Telegram Channel**:
   - Open Telegram
   - Click "New Channel"
   - Name: "Gujarati MCQ Questions"
   - Type: Public or Private
   - Click "Create"

5. **Add bot as admin**:
   - Open your channel
   - Click channel name → "Administrators"
   - Click "Add Administrator"
   - Search for your bot username
   - Add it with "Post Messages" permission

6. **Get Channel ID**:
   - If public channel: Use `@channelname` (e.g., `@gujarati_mcq`)
   - If private channel:
     - Forward any message from the channel to `@userinfobot`
     - It will show the channel ID (e.g., `-1001234567890`)
   - **SAVE THIS ID**

---

### Step 4: Setup GitHub Repository

1. **Fork or create repository**:
   - Create new repository on GitHub
   - Name it: `telegram-mcq-bot`
   - Make it private or public (your choice)

2. **Upload files**:
   - Upload all files from `telegram-bot/` folder:
     - `send_question.py`
     - `requirements.txt`
     - `SETUP.md` (this file)
   - Upload `.github/workflows/send-telegram-question.yml`

3. **Add GitHub Secrets**:
   - Go to repository "Settings" → "Secrets and variables" → "Actions"
   - Click "New repository secret"
   - Add these 3 secrets:

   **Secret 1: APPS_SCRIPT_URL**
   - Name: `APPS_SCRIPT_URL`
   - Value: Your Google Apps Script Web App URL
   - Example: `https://script.google.com/macros/s/AKfycbx.../exec`

   **Secret 2: TELEGRAM_BOT_TOKEN**
   - Name: `TELEGRAM_BOT_TOKEN`
   - Value: Your Telegram bot token
   - Example: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

   **Secret 3: TELEGRAM_CHANNEL_ID**
   - Name: `TELEGRAM_CHANNEL_ID`
   - Value: Your Telegram channel ID
   - Example: `@gujarati_mcq` or `-1001234567890`

---

### Step 5: Test the System

1. **Manual test**:
   - Go to "Actions" tab in GitHub
   - Click "Send Telegram MCQ Question"
   - Click "Run workflow" → "Run workflow"
   - Wait 30 seconds
   - Check your Telegram channel for the question

2. **Check logs**:
   - Click on the workflow run
   - Click "send-question" job
   - Review the logs for any errors

3. **Verify**:
   - ✅ Question appears in Telegram
   - ✅ Gujarati text displays correctly
   - ✅ Options are formatted properly
   - ✅ Correct answer is shown

---

## ⏰ Schedule Configuration

**Current schedule** (in `.github/workflows/send-telegram-question.yml`):
```yaml
- cron: '0 5,8,11,14,17 * * *'
```

This runs at:
- 10:30 AM IST
- 1:30 PM IST
- 4:30 PM IST
- 7:30 PM IST
- 10:30 PM IST (will be skipped by time check)

**To modify schedule**:
1. Edit the cron expression
2. Use https://crontab.guru/ for help
3. Remember: GitHub Actions uses UTC time
4. The Python script checks IST time (11 AM - 10 PM)

---

## 🎯 How It Works

```
┌─────────────────┐
│  Google Sheet   │ (Private, contains questions)
│  (Private)      │
└────────┬────────┘
         │
         │ Apps Script Web App
         │ (Executes as owner)
         ▼
┌─────────────────┐
│  Apps Script    │ Returns random question JSON
│  Web App        │
└────────┬────────┘
         │
         │ HTTPS GET
         ▼
┌─────────────────┐
│ GitHub Actions  │ Scheduled (UTC)
│  (Free)         │
└────────┬────────┘
         │
         │ Runs Python script
         ▼
┌─────────────────┐
│ Python Script   │ 1. Check IST time (11 AM - 10 PM)
│                 │ 2. Fetch question
│                 │ 3. Format message
│                 │ 4. Handle length limits
└────────┬────────┘
         │
         │ Telegram Bot API
         ▼
┌─────────────────┐
│ Telegram        │ Question posted!
│ Channel         │
└─────────────────┘
```

---

## 🔒 Security Features

1. **Google Sheet stays private** - Only accessible via Apps Script
2. **Apps Script executes as owner** - No public access to sheet
3. **Secrets stored in GitHub** - Not in code
4. **No credentials in logs** - Secure execution

---

## 📊 Message Handling Logic

### Case 1: Short Question (≤ 4096 chars)
```
❓ પ્રશ્ન:
[Question text]

A️⃣ [Option A]
B️⃣ [Option B]
C️⃣ [Option C]
D️⃣ [Option D]

✅ સાચો જવાબ: A

📘 સમજૂતી:
[Explanation]
```

### Case 2: Long Question (> 4096 chars)
**Message 1:**
```
❓ પ્રશ્ન:
[Question text]

📘 સમજૂતી:
[Explanation]
```

**Message 2 (Poll):**
```
વિકલ્પો પસંદ કરો:
○ [Option A]
○ [Option B]
○ [Option C]
● [Option D] ✓
```

---

## 🐛 Troubleshooting

### Issue: No questions appearing

**Check:**
1. GitHub Actions logs for errors
2. Apps Script URL is correct
3. Bot token is valid
4. Channel ID is correct
5. Bot is admin in channel
6. Current time is within IST 11 AM - 10 PM

### Issue: Gujarati text shows as boxes

**Solution:**
- This is a display issue on your device
- Telegram properly supports Gujarati
- Test on different device/app

### Issue: "403 Forbidden" error

**Solution:**
- Bot is not admin in channel
- Add bot as administrator with "Post Messages" permission

### Issue: Apps Script returns error

**Solution:**
1. Open Apps Script editor
2. Run `testGetRandomQuestion()` function
3. Check logs (View → Logs)
4. Verify sheet has data
5. Verify column order is correct

---

## 📈 Monitoring

**Check execution:**
1. Go to GitHub repository
2. Click "Actions" tab
3. See all workflow runs
4. Green ✓ = Success
5. Red ✗ = Failed (click to see logs)

**Check Telegram:**
- Questions should appear at scheduled times
- Only during IST 11 AM - 10 PM window

---

## 🎉 Success Checklist

- [ ] Google Sheet uploaded with correct columns
- [ ] Apps Script deployed as Web App
- [ ] Apps Script URL saved
- [ ] Telegram bot created
- [ ] Bot token saved
- [ ] Telegram channel created
- [ ] Bot added as channel admin
- [ ] Channel ID saved
- [ ] GitHub repository created
- [ ] All files uploaded
- [ ] 3 secrets added to GitHub
- [ ] Manual test successful
- [ ] Question appears in Telegram
- [ ] Gujarati text displays correctly

---

## 💡 Tips

1. **Test first**: Always run manual test before relying on schedule
2. **Monitor logs**: Check GitHub Actions logs regularly
3. **Backup sheet**: Keep backup of your Google Sheet
4. **Update schedule**: Adjust cron as needed
5. **Add more questions**: Just add rows to Google Sheet

---

## 🆓 Cost

**Total cost: ₹0 (100% FREE)**

- Google Apps Script: Free
- GitHub Actions: 2000 minutes/month free
- Telegram Bot API: Free
- Google Sheets: Free (15 GB storage)

---

## 📞 Support

If you encounter issues:
1. Check troubleshooting section
2. Review GitHub Actions logs
3. Test Apps Script manually
4. Verify all secrets are correct

---

**System is now ready! Questions will be posted automatically during IST 11 AM - 10 PM.** 🎉
