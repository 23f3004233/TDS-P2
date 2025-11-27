# Complete Setup Guide

## Step-by-Step Deployment Instructions

### Prerequisites Checklist

- [ ] Git installed
- [ ] GitHub account
- [ ] Railway account (sign up at railway.app)
- [ ] AIPipe token from aipipe.org/login
- [ ] Form submitted with secret and endpoint URL

### 1. Local Setup

```bash
# Clone your repository
cd /path/to/your/project

# Create all __init__.py files
touch app/__init__.py
touch app/utils/__init__.py
touch agents/__init__.py
touch processors/__init__.py
touch llm/__init__.py
touch tests/__init__.py

# Create .env file
cp .env.example .env

# Edit .env with your values
nano .env
# Add:
# AIPIPE_TOKEN=your_actual_token
# EMAIL=23f3004233@ds.study.iitm.ac.in
# QUIZ_SECRET=your_chosen_secret_string
# GITHUB_REPO=https://github.com/yourusername/your-repo
```

### 2. Fix Import in config.py

Open `app/config.py` and fix line 6:

```python
# Change this line:
from dotenv import load_load_dotenv()

# To this:
from dotenv import load_dotenv
load_dotenv()
```

### 3. Test Locally (Optional but Recommended)

```bash
# Make scripts executable
chmod +x run_local.sh
chmod +x test_deployment.sh

# Run locally
./run_local.sh

# In another terminal, test
./test_deployment.sh
```

### 4. Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Initial commit: LLM Quiz Solver"

# Push to GitHub
git push origin main
```

### 5. Deploy to Railway

#### 5.1 Create New Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect the Dockerfile

#### 5.2 Configure Environment Variables

In Railway dashboard:

1. Click on your service
2. Go to "Variables" tab
3. Add these variables:

```
AIPIPE_TOKEN=your_aipipe_token
EMAIL=23f3004233@ds.study.iitm.ac.in
QUIZ_SECRET=your_secret_string
GITHUB_REPO=https://github.com/yourusername/repo

PRIMARY_MODEL=openai/gpt-4o
VERIFIER_MODEL=anthropic/claude-sonnet-4
FALLBACK_MODELS=google/gemini-2.0-flash-exp,openai/gpt-4-turbo

QUIZ_TIMEOUT=180
REQUEST_TIMEOUT=30
BROWSER_TIMEOUT=60
MAX_FILE_SIZE_MB=50
MAX_RETRIES=3
ENABLE_VERIFICATION=true
LOG_LEVEL=INFO
```

#### 5.3 Deploy

Railway will automatically build and deploy. This takes 5-10 minutes.

#### 5.4 Get Your URL

Once deployed:
1. Click "Settings"
2. Under "Networking", click "Generate Domain"
3. Your URL will be: `https://your-app-name.up.railway.app`

### 6. Submit to Google Form

1. Go to the Google Form link from project description
2. Fill in:
   - Email: `23f3004233@ds.study.iitm.ac.in`
   - Secret: (your chosen secret string)
   - API Endpoint: `https://your-app-name.up.railway.app/quiz`
   - GitHub Repo: `https://github.com/yourusername/repo`

### 7. Test Your Deployment

```bash
# Test with your Railway URL
SERVER_URL=https://your-app-name.up.railway.app \
EMAIL=23f3004233@ds.study.iitm.ac.in \
SECRET=your_secret \
./test_deployment.sh
```

### 8. Monitor Logs

In Railway dashboard:
1. Click on your service
2. Go to "Deployments"
3. Click on active deployment
4. View logs in real-time

### 9. Pre-Evaluation Checklist

- [ ] Service is deployed and running
- [ ] Health endpoint responds: `https://your-url/health`
- [ ] Test with demo endpoint succeeds
- [ ] GitHub repo is public
- [ ] MIT LICENSE file exists in repo
- [ ] README.md is updated
- [ ] All environment variables are set
- [ ] Form is submitted with correct URL
- [ ] Logs show no errors

### Troubleshooting

#### Build Fails

**Error**: Dependency installation fails
**Solution**: Check requirements.txt format, ensure no version conflicts

**Error**: Playwright installation fails
**Solution**: Railway should have enough memory. Check Dockerfile.

#### Runtime Errors

**Error**: `AIPIPE_TOKEN not found`
**Solution**: Double-check environment variables in Railway

**Error**: `403 Forbidden`
**Solution**: Verify secret matches what you submitted in form

**Error**: Browser timeout
**Solution**: Increase `BROWSER_TIMEOUT` to 90 or 120

#### Performance Issues

**Slow Processing**: 
- Disable verification: `ENABLE_VERIFICATION=false`
- Use faster models: `PRIMARY_MODEL=google/gemini-2.0-flash-exp`

**Memory Issues**:
- Railway free tier: 512MB RAM
- Upgrade to hobby plan if needed ($5/month)

### Important Notes

1. **Evaluation Window**: Nov 29, 2025, 3:00-4:00 PM IST
2. **Time Limit**: 3 minutes per quiz
3. **Keep Service Running**: Ensure no downtime during evaluation
4. **Monitor Costs**: Check AIPipe usage at aipipe.org/usage

### Emergency Contacts

If issues during evaluation:
1. Check Railway logs immediately
2. Restart service if needed (Railway dashboard → Restart)
3. Verify environment variables are set

### Post-Evaluation

After evaluation, you can:
1. Review logs in Railway
2. Check AIPipe usage and costs
3. Analyze performance metrics
4. Improve based on actual quiz questions

---

## Quick Reference

### Railway Commands

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# View logs
railway logs

# Restart service
railway restart
```

### Useful Endpoints

- Health: `GET /health`
- Root: `GET /`
- Quiz: `POST /quiz`

### Environment Check

```bash
# Check all env vars are set
railway variables
```

Good luck with your evaluation! 🚀