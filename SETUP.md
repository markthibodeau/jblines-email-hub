# JBLines Email Hub — Setup Guide

This guide walks you through deploying your Email Hub from scratch.
**No technical experience required.** Each step is written in plain English.

Estimated time: **90–120 minutes** (most of it is waiting for things to load)

---

## What You'll Set Up

| Service | Purpose | Cost |
|---|---|---|
| **GitHub** | Stores your code | Free |
| **Neon** | Your database (stores all emails) | Free |
| **Render** | Runs your backend/AI server | Free |
| **Vercel** | Hosts your team's web dashboard | Free |
| **Google Cloud** | Connects to Gmail | Free |
| **Anthropic** | Powers the Claude AI features | Pay per use (~$5–15/mo) |

---

## STEP 1 — Upload Your Code to GitHub

GitHub is where your code lives. Render and Vercel will automatically pull from it.

1. Go to [github.com](https://github.com) and create a free account (if you don't have one)
2. Click the **+** button in the top right → **New repository**
3. Name it `jblines-email-hub` → click **Create repository**
4. Download and install [GitHub Desktop](https://desktop.github.com) — it's the easiest way to upload code
5. Open GitHub Desktop → **File → Add Local Repository**
6. Navigate to the `email-hub` folder you received → click **Add Repository**
7. Click **Publish repository** → uncheck "Keep this code private" only if you want it public (keep it private is fine)
8. Click **Publish Repository** ✅

---

## STEP 2 — Create Your Database (Neon)

Neon is a free PostgreSQL database that stores all your emails, customers, billing, and meetings.

1. Go to [neon.tech](https://neon.tech) → **Sign up free** (use your Google account)
2. Click **New Project** → name it `jblines-email-hub` → choose region **US East** → click **Create**
3. On the next screen, click **Connection string** and copy the full string that looks like:
   ```
   postgresql://username:password@ep-something.us-east-2.aws.neon.tech/neondb
   ```
4. **Save this string** — you'll paste it into Render in Step 4

---

## STEP 3 — Get Your Anthropic API Key

This powers the AI classification and chat features.

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account → go to **API Keys** → click **Create Key**
3. Name it `jblines-email-hub` → copy the key (starts with `sk-ant-...`)
4. **Save this key** — you'll need it in Step 4

---

## STEP 4 — Set Up Google Service Account (Gmail Access)

This is the most involved step. It lets the system read all your company inboxes without individual logins.

### 4a — Create a Google Cloud Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown at the top → **New Project**
3. Name it `JBLines Email Hub` → click **Create**
4. Make sure the new project is selected in the dropdown

### 4b — Enable Gmail API
1. In the search bar, type **Gmail API** → click it
2. Click **Enable** ✅

### 4c — Create a Service Account
1. In the left menu: **IAM & Admin → Service Accounts**
2. Click **+ Create Service Account**
3. Name: `email-hub-sync` → click **Create and Continue** → click **Done**
4. Click on the service account you just created
5. Go to the **Keys** tab → **Add Key → Create New Key → JSON** → click **Create**
6. A `.json` file will download automatically — **keep this safe, it's like a password**
7. Open the JSON file in Notepad — select ALL the text → Copy it

### 4d — Enable Domain-Wide Delegation
1. Still on the service account page → click **Edit** (pencil icon)
2. Check **Enable Google Workspace Domain-wide Delegation** → Save
3. Copy the **Client ID** number that appears (looks like: `123456789012345678901`)

### 4e — Authorize in Google Workspace Admin
> ⚠️ You need Google Workspace admin access for this step. This is your Google Admin console, not your regular Gmail.

1. Go to [admin.google.com](https://admin.google.com)
2. **Security → Access and data control → API controls**
3. Click **Manage Domain Wide Delegation → Add new**
4. **Client ID**: paste the number from step 4d
5. **OAuth Scopes**: paste these two scopes:
   ```
   https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify
   ```
6. Click **Authorize** ✅

---

## STEP 5 — Deploy the Backend (Render)

1. Go to [render.com](https://render.com) → **Sign up** with your GitHub account
2. Click **New → Web Service**
3. Connect your GitHub repo: `jblines-email-hub`
4. Set the **Root Directory** to: `backend`
5. Set **Runtime** to: `Docker`
6. Click **Create Web Service**
7. Go to the **Environment** tab and add these variables (click **Add Environment Variable** for each):

| Key | Value |
|---|---|
| `DATABASE_URL` | Your Neon connection string from Step 2 (replace `postgresql://` with `postgresql+asyncpg://`) |
| `ANTHROPIC_API_KEY` | Your Anthropic key from Step 3 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The entire contents of the JSON file from Step 4c (paste as one line) |
| `COMPANY_INBOXES` | `sales@jblines.com,support@jblines.com,billing@jblines.com` (add all your inboxes) |
| `PRIVATE_INBOXES` | `mark@jblines.com,ben@jblines.com` |
| `SYNC_DAYS_BACK` | `180` |
| `JWT_SECRET_KEY` | Any long random string (e.g. `jblines-super-secret-key-2024-xyz`) |
| `SETUP_SECRET` | A temporary password you'll use once to create your admin account |

8. Click **Save Changes** → Render will build and deploy (takes 3–5 minutes)
9. When it shows **Live**, copy your Render URL — it looks like: `https://jblines-email-hub-xxxx.onrender.com`

---

## STEP 6 — Create Your Admin Account

Once the backend is live:

1. Open a new browser tab and go to:
   ```
   https://YOUR-RENDER-URL.onrender.com/api/auth/setup
   ```
   Replace `YOUR-RENDER-URL` with your actual Render URL.

2. You need to call this endpoint with your details. The easiest way is to use [Hoppscotch](https://hoppscotch.io):
   - Go to hoppscotch.io
   - Method: **POST**
   - URL: `https://YOUR-RENDER-URL.onrender.com/api/auth/setup`
   - Body (JSON):
     ```json
     {
       "email": "mark@jblines.com",
       "name": "Mark",
       "password": "your-setup-secret-from-step-5",
       "role": "admin"
     }
     ```
   - Click **Send**
   - You should get back: `{"message": "Admin account created"}`

3. Repeat for Ben, but log in first and use the `/api/auth/register` endpoint instead

---

## STEP 7 — Deploy the Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) → **Sign up** with your GitHub account
2. Click **Add New → Project**
3. Import your `jblines-email-hub` repo
4. Set **Root Directory** to: `frontend`
5. Under **Environment Variables**, add:

| Key | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | Your Render URL from Step 5 (e.g. `https://jblines-email-hub-xxxx.onrender.com`) |

6. Click **Deploy** → wait 2–3 minutes
7. Vercel will give you a URL like: `https://jblines-email-hub.vercel.app` — **this is your team's dashboard URL** 🎉

---

## STEP 8 — First Login & Share With Your Team

1. Go to your Vercel URL
2. Log in with `mark@jblines.com` and your password
3. The initial email sync will start automatically — it runs in the background
4. To add team members: go to **Admin → Users** → click the button to invite

### Giving team members access:
- Log in as admin
- Call `POST /api/auth/register` with each person's email, name, and a temporary password
- They can change their password later (coming in v2)
- Staff accounts **cannot** see raw email content from your or Ben's inbox

---

## STEP 9 — Configure Your Custom Domain (Optional)

Want `hub.jblines.com` instead of the Vercel URL?

1. In Vercel: **Project Settings → Domains → Add**
2. Enter your domain (e.g. `hub.jblines.com`)
3. Vercel will show you a DNS record to add at your domain registrar
4. Add the record → wait 10 minutes → done ✅

---

## Troubleshooting

**Backend shows "Application error" on Render:**
→ Click **Logs** in Render — the error message will tell you exactly what's wrong (usually a missing environment variable)

**Emails not syncing:**
→ Go to `https://YOUR-RENDER-URL/api/admin/sync-status` — it shows the status of each inbox

**"Unauthorized" when logging in:**
→ Make sure `JWT_SECRET_KEY` is set in Render environment variables

**Google delegation not working:**
→ Double-check Step 4e — the scopes must be entered exactly as shown, comma-separated

---

## Monthly Costs (After Free Tiers)

| Service | Free Tier Limit | Overage Cost |
|---|---|---|
| Neon | 500MB database | ~$19/mo for more |
| Render | 750 hours/month | $7/mo for always-on |
| Vercel | 100GB bandwidth | Rarely exceeded |
| Anthropic Claude | None — pay per use | ~$5–20/mo typical |

**Total estimated cost: $0–$27/month** depending on email volume.

---

## Need Help?

Come back to this conversation and tell me what step you're on — I can walk you through any part of this in real time.
