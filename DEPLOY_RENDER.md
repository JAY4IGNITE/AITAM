# 🚀 Deploying ThreatLens to Render

ThreatLens is fully configured for deployment on [Render](https://render.com) using the included `render.yaml` Blueprint or manual setup.

---

## ⚡ Option 1: One-Click Blueprint Deployment (Recommended)

1. Push your code to your GitHub / GitLab repository.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** → **Blueprint**.
4. Connect your ThreatLens GitHub repository.
5. Render will automatically read `render.yaml` and configure:
   - **`threatlens-api`** (FastAPI Python 3.11 Web Service)
   - **`threatlens-ui`** (React Vite SPA Static Site with client-side routing)
6. Under **Environment Variables**, fill in your keys:
   - `DATABASE_URL`: `postgresql://postgres.crrlmgpdzatcwdpvunte:JAYAsai%40514@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres`
   - `GOOGLE_SAFE_BROWSING_API_KEY`: `AIzaSyDjSBqocJZsGOAc2YjubuaMuUAmT3mKOBs`
   - `VIRUSTOTAL_API_KEY`: `7cfbd99eb7de50ecbe08d316943441c029e719733d7101322feae80a00e6ed0e`
   - `URLHAUS_AUTH_KEY`: `d7bd377869bf1ed56a3c94b8a87eecaefb3f2adcf68e9ca5`
7. Click **Apply**. Render will build and deploy both services!

---

## 🛠️ Option 2: Manual Dashboard Setup

### Step 1: Deploy the Backend Web Service

1. On Render, click **New +** → **Web Service**.
2. Connect your Git repository.
3. Configure the following fields:
   - **Name:** `threatlens-api`
   - **Region:** Choose closest to your database (e.g. `Oregon` or `Singapore` / `Tokyo` for `ap-northeast-1`)
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3` (or `Docker`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variables**:
   | Variable | Value |
   | :--- | :--- |
   | `DATABASE_URL` | `postgresql://postgres.crrlmgpdzatcwdpvunte:JAYAsai%40514@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres` |
   | `GOOGLE_SAFE_BROWSING_API_KEY` | `AIzaSyDjSBqocJZsGOAc2YjubuaMuUAmT3mKOBs` |
   | `VIRUSTOTAL_API_KEY` | `7cfbd99eb7de50ecbe08d316943441c029e719733d7101322feae80a00e6ed0e` |
   | `URLHAUS_AUTH_KEY` | `d7bd377869bf1ed56a3c94b8a87eecaefb3f2adcf68e9ca5` |
   | `CORS_ORIGINS` | `*` |
   | `JWT_SECRET` | *(Generate any random string)* |
5. Click **Create Web Service**.

---

### Step 2: Deploy the Frontend Static Site

1. On Render, click **New +** → **Static Site**.
2. Connect your Git repository.
3. Configure the following fields:
   - **Name:** `threatlens-ui`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. Add **Redirects / Rewrites** (under settings):
   - **Type:** `Rewrite`
   - **Source:** `/*`
   - **Destination:** `/index.html`
5. Click **Create Static Site**.

---

## 🔒 Verification & Health Check

Once deployed, you can verify your service:
- **Backend Health Check:** `https://your-api-name.onrender.com/api/health`
- **SOC Dashboard:** `https://your-ui-name.onrender.com`
