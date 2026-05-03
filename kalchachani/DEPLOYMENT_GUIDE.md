# कलचाचणी 2025-26 — Complete Deployment Guide
## How to Conduct the Test & Share It With Students Over the Internet

---

## What You Need First (One-Time Setup)

1. **A computer or laptop** (Windows, Mac, or Linux) — your phone alone won't work as the server
2. **Python 3.10+** — download free from https://python.org
3. **A free account on Render.com** (recommended) or Railway.app — for the public internet link

---

## OPTION 1 — Deploy on Render.com (FREE, Permanent Public URL)
### ✅ Best option — students anywhere in Maharashtra can access it

### Step 1 — Put your files in a folder like this:
```
kalchachani/
├── app.py
├── requirements.txt
└── templates/
    └── kalchachani_test.html
```

Create a file called `requirements.txt` with this content:
```
flask
flask-cors
matplotlib
numpy
gunicorn
```

### Step 2 — Upload to GitHub (free)
1. Create a free account at https://github.com
2. Click **New repository** → name it `kalchachani` → click **Create**
3. Upload your files by dragging them into the GitHub webpage
   - Drag `app.py` and `requirements.txt` to the root
   - Create a folder called `templates` and upload `kalchachani_test.html` inside it
4. Click **Commit changes**

### Step 3 — Deploy on Render.com
1. Go to https://render.com → Sign up free (use Google or GitHub login)
2. Click **New +** → **Web Service**
3. Connect your GitHub account → Select your `kalchachani` repository
4. Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | kalchachani-2025 |
| **Environment** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Plan** | Free |

5. Click **Create Web Service**
6. Wait 2–3 minutes for the first deploy to finish
7. You'll get a URL like: `https://kalchachani-2025.onrender.com`

### Step 4 — Share with students
Your permanent test link is:
```
https://kalchachani-2025.onrender.com/test
```
Share this via **WhatsApp, school notice board, SMS, or email**.

Your admin dashboard (for teachers only):
```
https://kalchachani-2025.onrender.com/admin?pw=kalchachani2025
```

> ⚠️ **Important:** Free Render plan goes to sleep after 15 minutes of inactivity.
> The first student to open the link may wait 20–30 seconds for it to wake up — after that it's fast.
> To prevent sleep, keep the tab open on your school computer during the test session.

---

## OPTION 2 — Railway.app (FREE, Faster Than Render)

1. Go to https://railway.app → Sign up free with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `kalchachani` repository
4. Railway auto-detects Python — set **Start Command**: `gunicorn app:app`
5. Go to **Settings → Domains** → click **Generate Domain**
6. Your URL: `https://kalchachani-xxxx.up.railway.app`
7. Share `/test` link with students

> Railway free plan gives 500 hours/month — enough for a full school year of testing sessions.

---

## OPTION 3 — ngrok (Quick, No Account Needed for Short Sessions)
### ✅ Best if you just want to run the test for one class period today

This runs the server on **your laptop** and gives a public internet link for ~8 hours.

### Step 1 — Install and run the server
```bash
pip install flask flask-cors matplotlib numpy
python app.py
```
You'll see: `Running on http://localhost:5000`

### Step 2 — Install ngrok
Go to https://ngrok.com/download → download for your OS → unzip it

### Step 3 — Start ngrok
Open a second terminal window and run:
```bash
# Windows
ngrok.exe http 5000

# Mac / Linux
./ngrok http 5000
```

You'll see something like:
```
Forwarding   https://abc123def456.ngrok-free.app → localhost:5000
```

### Step 4 — Share the link
Send students: `https://abc123def456.ngrok-free.app/test`

They can open this on their phone, tablet, or computer from anywhere.

> ⚠️ The ngrok link changes every time you restart it (free plan).
> Keep your laptop running and the server open until all students finish.
> If your laptop sleeps or loses internet, the link breaks.

---

## OPTION 4 — Same Wi-Fi / School Computer Lab
### ✅ Use this if all students are in the same school building

1. Run the server on the teacher's computer: `python app.py`
2. Find the teacher's computer's IP address:
   - **Windows:** Open Command Prompt → type `ipconfig` → look for `IPv4 Address` (e.g. `192.168.1.5`)
   - **Mac:** System Preferences → Network → shows IP
3. Share this link with students: `http://192.168.1.5:5000/test`
4. Students on the same school Wi-Fi open this on their phone browser

---

## Setting Up the Test Session (Day-of Guide for Teachers)

### Before the Session
- [ ] Deploy your app (Render/Railway) or start the local server (ngrok/local)
- [ ] Test the link yourself on your phone — make sure it loads
- [ ] Prepare a short announcement for students (see template below)
- [ ] Keep the admin dashboard open in a separate browser tab
- [ ] Inform students this will take 50–60 minutes — schedule accordingly

### Student Announcement Template (WhatsApp/Notice Board)
```
📋 कलचाचणी 2025-26 — करिअर मार्गदर्शन चाचणी

प्रिय विद्यार्थी,

खालील लिंकवर तुमची कलचाचणी सादर करा:
👉 [YOUR LINK HERE]/test

📱 मोबाईलवर Chrome किंवा Safari मध्ये उघडा
⏱ साधारण 50-60 मिनिटे लागतात
📅 अंतिम मुदत: [DATE]

प्रश्न असल्यास शिक्षकांशी संपर्क करा.

---
Dear Students,
Complete your Kalchachani career aptitude test at the link above.
Open in Chrome or Safari on your phone/computer.
Takes approx 50-60 minutes. Deadline: [DATE]
```

### During the Session
- Students can take the test from home, school, or anywhere with internet
- Each student gets a **unique Reference ID** after submitting — tell them to note it
- You can watch submissions coming in live at `/admin?pw=kalchachani2025`
- The admin dashboard shows each student's name, school, district, and top interest group in real time

### After the Session
- Open admin dashboard → click **View** or **Download** next to each student
- The report opens as a printable HTML page with all charts
- **Print to PDF** using Ctrl+P (or Cmd+P on Mac) for paper reports
- Share individual report links with class teachers/counsellors

---

## Changing the Admin Password (Recommended Before Going Live)

**On Render.com:**
1. Go to your Render dashboard → your service → **Environment**
2. Add environment variable: `ADMIN_PASSWORD` = `YourSecretPassword`
3. Click **Save Changes** → Render automatically redeploys

**On Railway:**
1. Go to your service → **Variables**
2. Add: `ADMIN_PASSWORD` = `YourSecretPassword`

**Locally:**
```bash
# Mac / Linux
export ADMIN_PASSWORD=YourSecretPassword
python app.py

# Windows Command Prompt
set ADMIN_PASSWORD=YourSecretPassword
python app.py
```

---

## Making Your Data Permanent on Render (Important!)

Render's free plan has **ephemeral storage** — if the server restarts, the `results/` folder is deleted.

**Solution: Download all results before the server restarts.**

After each test session:
1. Go to admin dashboard
2. Click **Download** for each student's report
3. Save the HTML files on your computer or Google Drive

**OR** — for a permanent database, upgrade to Render's paid plan ($7/month) which has persistent disk.

---

## Summary: Which Option to Use?

| Your Situation | Best Option |
|----------------|-------------|
| Want a permanent link all year | Render.com or Railway.app (free) |
| Just need it for one class today | ngrok (local server) |
| All students are in the same school | Same Wi-Fi (local IP) |
| Large school, many classes, all year | Railway.app (more reliable free tier) |

---

## Question Count Summary

| Section | Questions | What It Measures |
|---------|-----------|-----------------|
| 1 — रुची परीक्षण | Q1–Q42 (7 groups × 6) | Career interest in each of 7 groups |
| 2 — विषय क्षमता | Q43–Q54 (6 subjects × 2) | Subject aptitude & enjoyment |
| 3 — व्यक्तिमत्त्व | Q55–Q72 (6 traits × 3) | Personality profile |
| 4 — कौशल्ये | Q73–Q84 (6 skills × 2) | Skill strengths |
| 5 — मूल्ये | Q85–Q92 (8) | Career values & work environment |
| 6 — शिकण्याची पद्धत | Q93–Q100 (8) | Learning & thinking style |
| 7 — करिअर जागरूकता | Q101–Q120 (20) | Career awareness, preferences, concerns |
| **Total** | **120 scored + 1 optional open reflection** | |

---

## Troubleshooting

**"The link doesn't open on my phone"**
→ Make sure students use Chrome or Safari, not an in-app browser (e.g. WhatsApp's built-in browser)
→ Tell them to tap the ⋮ menu → "Open in Chrome"

**"It says 'Application Error' on Render"**
→ Go to Render dashboard → Logs → look for the error
→ Most common cause: missing `gunicorn` in requirements.txt — make sure it's there

**"Students submitted but I can't see reports"**
→ Check Render's ephemeral storage warning above — download reports after each session

**"The ngrok link stopped working"**
→ Your laptop went to sleep or lost internet — restart ngrok and share the new link

**"Marathi font not showing correctly"**
→ The font loads from Google Fonts — students need internet. Works on all modern Android & iPhone browsers.

---

*कलचाचणी 2025-26 · महाराष्ट्र राज्य माध्यमिक व उच्च माध्यमिक शिक्षण मंडळ*
