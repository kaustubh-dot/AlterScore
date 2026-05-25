# AlterScore Permanently Free Hosting Strategy

Hosting Python machine learning backends for completely free, permanently, can be challenging since popular platforms like Heroku and Railway have retired or limited their free credits. 

Below are the **best 4 strategies** to host the AlterScore FastAPI backend permanently for free, ranked by power and ease of use.

---

## Strategy 1: Hugging Face Spaces (Docker) // ⭐ RECOMMENDED
Hugging Face Spaces is the **absolute best-kept secret** for hosting Python ML backends permanently and completely for free.

* **The Free Tier Specs:**
  * **2 vCPUs** and a massive **16GB of RAM** (permanently free).
  * 50GB of disk space.
* **Why it fits AlterScore:**
  * Since our FastAPI backend runs standard Python ML packages, we can wrap the backend in a standard `Dockerfile` and host it as a **Docker Space**.
  * The 16GB of RAM is more than enough to load all explainers, preprocessors, and even run the neural models (TabNet/MLP) if needed.
* **How to deploy:**
  1. Create a free account at [huggingface.co](https://huggingface.co).
  2. Click **New > Space**.
  3. Set Space SDK to **Docker** (Blank template).
  4. Create a `Dockerfile` at your repository root:
     ```dockerfile
     FROM python:3.12-slim
     WORKDIR /code
     COPY backend/requirements.txt .
     RUN pip install --no-cache-dir -r requirements.txt
     COPY . .
     EXPOSE 7860
     CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
     ```
  5. Push your code to the Hugging Face Git remote. It will automatically build and expose a public HTTPS URL (e.g. `https://username-space-name.hf.space/api`).
* **Note on sleeping:** HF Spaces pause (sleep) after 48 hours of zero traffic. Visiting the URL instantly wakes it up in 5–10 seconds, or you can ping it daily using a free uptime monitor (like UptimeRobot) to keep it awake 24/7.

---

## Strategy 2: Koyeb Free Tier // ⚡ 24/7 Free Container
Koyeb is a modern developer platform that offers a permanently free tier that **does not spin down (no sleeping)**.

* **The Free Tier Specs:**
  * **512MB RAM**, 0.1 CPU, and 2GB SSD (permanently free in Washington D.C., Frankfurt, or Singapore).
  * Runs 24/7 with zero cold starts.
* **Why it fits AlterScore:**
  * Since we optimized the serving manifest to run **monotonic XGBoost** (instead of heavy PyTorch), our memory footprint at startup is only about **120MB**, which fits comfortably inside Koyeb's 512MB RAM limit.
* **How to deploy:**
  1. Sign up at [koyeb.com](https://koyeb.com).
  2. Click **Create Service**, connect your GitHub account, and select your AlterScore repository.
  3. Configure the build:
     * **Build Command:** `pip install -r backend/requirements.txt` (Vercel/Koyeb handle this natively).
     * **Run Command:** `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`.
     * **Port:** `8000`.
  4. Koyeb builds the container and hosts it continuously for free.

---

## Strategy 3: Render Free Tier // 🔄 Free with Keep-Alive
Render offers a permanently free web service tier, but it automatically spins down (sleeps) after 15 minutes of inactivity.

* **The Free Tier Specs:**
  * **512MB RAM** and 0.1 CPU.
* **The Drawback (Cold Starts):**
  * If a borrower visits the frontend after the backend has gone to sleep, the first score request will hang for **50 seconds to 2 minutes** while Render boots the container and verifies model checksums.
* **How to bypass (Keep-Alive Cron):**
  * You can keep the Render container awake 24/7 by setting up a free cron job on a service like [UptimeRobot.com](https://uptimerobot.com) or [Cron-job.org](https://cron-job.org) to ping your backend health endpoint (`https://your-app.onrender.com/api/health`) every **10 minutes**. This prevents the server from sleeping.

---

## Strategy 4: Oracle Cloud Free Tier // 💪 Always Free Virtual Machine
Oracle Cloud offers the most generous always-free virtual machine package on the market.

* **The Free Tier Specs:**
  * **4 ARM Ampere CPUs** and **24GB of RAM**!
  * 200GB of block storage.
* **Why it fits AlterScore:**
  * This is a full-fledged Ubuntu virtual machine. You get complete root access to run a persistent Docker container, a reverse proxy (Nginx), and save local JSONL prediction logs permanently.
* **Limitations:**
  * It is slightly harder to set up (requires SSH and Linux command line knowledge).
  * Creating a free account requires a credit card verification (though you are never charged).
