# Deploy Payment Reconciliation System to Streamlit Cloud

## Step 1: Prepare Repository for Deployment

### 1.1 Verify Git Repository
```bash
cd d:\OneLab\payment-reconciliation
git status
```

Repository should show:
- Branch: main or master
- Remote: origin pointing to GitHub

### 1.2 Verify All Files Ready
Ensure these files exist:
- ✅ app.py (main application)
- ✅ reconciliation.py (engine)
- ✅ data_generator.py (sample data)
- ✅ requirements.txt (dependencies)
- ✅ tests/test_reconciliation.py (tests)
- ✅ data/ folder with CSV files
- ✅ .gitignore (configured)

### 1.3 Update requirements.txt
Verify it contains:
```
streamlit==1.40.2
pandas==2.2.3
plotly==5.24.1
pytest==8.2.1
pytest-cov==6.0.0
numpy>=1.24.0
python-dateutil>=2.8.2
```

## Step 2: Push to GitHub

### 2.1 Add All Files
```bash
git add .
```

### 2.2 Commit Changes
```bash
git commit -m "Payment Reconciliation System - Ready for Streamlit Cloud deployment"
```

### 2.3 Push to GitHub
```bash
git push -u origin main
```
(Replace 'main' with your branch name if different)

### 2.4 Verify on GitHub
Visit: https://github.com/YOUR_USERNAME/payment-reconciliation
- Confirm all files are visible
- Confirm data/ folder with CSV files is there
- Confirm requirements.txt is present

## Step 3: Deploy to Streamlit Cloud

### 3.1 Sign Up (if not already done)
1. Go to: https://streamlit.io/cloud
2. Click "Sign up"
3. Select "Continue with GitHub"
4. Authorize Streamlit to access your repositories

### 3.2 Create New App
1. Click "Create app" on Streamlit Cloud dashboard
2. Select repository: `payment-reconciliation`
3. Select branch: `main` (or your branch)
4. Select main file: `app.py`
5. Click "Deploy"

### 3.3 Wait for Deployment
- First deployment takes 2-3 minutes
- Streamlit installs dependencies from requirements.txt
- App automatically starts

### 3.4 Access Your App
URL format: `https://payment-reconciliation-RANDOMSTRING.streamlit.app`

View in: https://share.streamlit.io/YOUR_USERNAME/payment-reconciliation/app.py

## Step 4: Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'reconciliation'"
**Solution**: Ensure all .py files are in root directory, not in subdirectories

### Issue: "FileNotFoundError: data/payment_platform_202411.csv"
**Solution**: 
1. Ensure data/ folder is committed to GitHub
2. Verify .gitignore doesn't exclude data/*.csv
3. Use "Load Sample Data" button to generate files at runtime

### Issue: "Missing required columns"
**Solution**: 
1. Check CSV files are properly formatted
2. Use "Load Sample Data" button to regenerate
3. Verify column names have no extra spaces

### Issue: App is slow to load
**Solution**: 
1. First load takes longer (dependencies installing)
2. Subsequent loads are faster
3. Streamlit Cloud caches dependencies

### View Logs
Click "Manage app" → "View logs" to see error messages

## Step 5: Share Your App

### Share URL
Send this link to anyone:
```
https://payment-reconciliation-RANDOMSTRING.streamlit.app
```

### Embed in Portfolio
Add to GitHub README:
```markdown
## Live Demo
[View Payment Reconciliation System](https://payment-reconciliation-RANDOMSTRING.streamlit.app)
```

### Direct GitHub Link
For easy access:
```
https://github.com/YOUR_USERNAME/payment-reconciliation
```

## Step 6: Deployment Checklist

✅ Git repository initialized
✅ All files committed to GitHub
✅ requirements.txt has all dependencies
✅ data/ folder included with CSV files
✅ app.py is main entry point
✅ .gitignore properly configured
✅ Streamlit Cloud account created
✅ App deployed successfully
✅ All 4 test scenarios working
✅ Dashboard loads and runs reconciliation
✅ CSV uploads work
✅ Sample data loads
✅ Reports download
✅ Share link works

## Step 7: Post-Deployment Testing

1. **Load Dashboard**
   - KPI cards display
   - Charts render
   - Test cases show status

2. **Load Sample Data**
   - Click "Load Sample Data" button
   - 19 platform + 18 bank records load
   - No errors displayed

3. **Run Reconciliation**
   - Click "Run Reconciliation"
   - Results display
   - Matched records table appears

4. **Check Discrepancies**
   - All 4 scenarios detected
   - Filters work
   - Download buttons active

5. **Download Reports**
   - CSV files download
   - Data is correct
   - No corruption

## Quick Reference Commands

```bash
# Clone repo locally
git clone https://github.com/YOUR_USERNAME/payment-reconciliation

# Test locally before deploying
streamlit run app.py

# Run tests
python -m pytest -v

# Generate fresh sample data
python data_generator.py

# View git log
git log --oneline

# Check remote
git remote -v
```

## Environment Variables (Optional)

If you need to add secrets later:
1. Go to Streamlit Cloud app dashboard
2. Click "Settings" → "Secrets"
3. Add secrets in TOML format
4. Access in code via: `st.secrets["key_name"]`

Example:
```toml
database_url = "postgresql://..."
api_key = "sk_..."
```

## Support & Documentation

- Streamlit Docs: https://docs.streamlit.io
- Streamlit Cloud: https://streamlit.io/cloud
- GitHub Issues: https://github.com/streamlit/streamlit/issues
- Streamlit Community: https://discuss.streamlit.io

## Success!

Once deployed, your Payment Reconciliation System will be:
- ✅ Publicly accessible
- ✅ Automatically updated when you push to GitHub
- ✅ Running on Streamlit's infrastructure
- ✅ Available 24/7

Share the live link with your assessment reviewers!
