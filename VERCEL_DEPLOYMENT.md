# Vercel Deployment Guide

## Overview

This project deploys to Vercel with:
- **Database**: Neon PostgreSQL (free 512MB)
- **File Storage**: Google Cloud Storage (free 15GB - same as Gmail!)
- **App Hosting**: Vercel serverless

---

## Step 1: Create Free Database (Neon PostgreSQL)

1. Go to https://neon.tech
2. Sign up with your Gmail account
3. Create a new project
4. Copy the connection string (looks like: `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname`)
5. Save this - you'll need it for Vercel environment variables

---

## Step 2: Set Up Google Cloud Storage (15GB Free!)

This is where your uploaded PDFs and documents will be stored.

### Quick Setup (Run the script):
```bash
python setup_gcloud.py
```

### Manual Setup:

#### 2.1 Create Google Cloud Project
1. Go to: https://console.cloud.google.com
2. Sign in with your Gmail account
3. Click "Select a project" → "New Project"
4. Name: "rgcet-uploads"
5. Click "Create"

#### 2.2 Enable Cloud Storage API
1. Go to: https://console.cloud.google.com/apis/library/storage-api.googleapis.com
2. Click "Enable"

#### 2.3 Create Storage Bucket
1. Go to: https://console.cloud.google.com/storage/browser
2. Click "Create Bucket"
3. Name: "rgcet-uploads" (must be globally unique)
4. Location: "Region" → "us-central1" (or closest to you)
5. Storage class: "Standard"
6. Access control: "Uniform"
7. Click "Create"

#### 2.4 Make Bucket Public
1. Go to your bucket in Cloud Storage
2. Click "Permissions" tab
3. Click "Grant Access"
4. Add members: "allUsers"
5. Role: "Storage Object Viewer"
6. Click "Save"

#### 2.5 Create Service Account
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "Create Service Account"
3. Name: "rgcet-uploads"
4. Click "Create and Continue"
5. Role: "Storage Admin"
6. Click "Done"

#### 2.6 Create Service Account Key
1. Click on your service account name
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON"
5. Click "Create"
6. Save the JSON file somewhere safe!

---

## Step 3: Push to GitHub

```bash
cd "C:\Users\mkail\Music\sai mam said project"
git init
git add .
git commit -m "Initial commit for Vercel deployment"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

---

## Step 4: Deploy to Vercel

1. Go to https://vercel.com
2. Sign up with your Gmail account
3. Click "New Project"
4. Import your GitHub repository
5. Framework Preset: "Other"
6. Root Directory: ./
7. Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
8. Output Directory: staticfiles
9. Install Command: `pip install -r requirements.txt`

---

## Step 5: Set Environment Variables in Vercel

Go to your Vercel project → Settings → Environment Variables and add:

### Required Variables:
```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.vercel.app
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname
CSRF_TRUSTED_ORIGINS=https://your-app.vercel.app
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

### Google Cloud Storage Variables:
```
GS_BUCKET_NAME=rgcet-uploads
GS_PROJECT_ID=your-project-id
GS_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GS_PRIVATE_KEY_ID=from-json-key-file
GS_PRIVATE_KEY=from-json-key-file
GS_CLIENT_ID=from-json-key-file
```

---

## Step 6: Run Migrations

After deployment, run migrations on your local machine with the production database:

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Pull environment variables
vercel env pull .env.local

# Run migrations
python manage.py migrate --settings=config.settings.vercel

# Create admin user
python manage.py createsuperuser --settings=config.settings.vercel

# Seed demo data
python manage.py seed_demo_data --settings=config.settings.vercel
```

---

## Step 7: Upload Test

1. Visit https://your-app.vercel.app
2. Login with: admin / RGCET@2026
3. Go to Resources → Upload a PDF or document
4. The file will be stored in Google Cloud Storage
5. Check: https://console.cloud.google.com/storage/browser/rgcet-uploads/media/

---

## How File Uploads Work

| Step | What Happens |
|------|--------------|
| 1 | User selects file in browser |
| 2 | Vercel receives the file in serverless function |
| 3 | Django saves file to Google Cloud Storage |
| 4 | File URL stored in PostgreSQL database |
| 5 | When user downloads, Django generates GCS URL |
| 6 | Browser downloads directly from Google Cloud |

**Your uploaded PDFs and documents are stored permanently in Google Cloud Storage (15GB free)!**

---

## Cost Breakdown

| Service | Free Tier | Your Usage |
|---------|-----------|------------|
| Vercel | 100GB bandwidth | College app = ~1GB/month |
| Neon PostgreSQL | 512MB storage | ~50MB for records |
| Google Cloud Storage | 15GB storage | ~5GB for PDFs/docs |
| **Total** | **$0/month** | **Free!** |

---

## Troubleshooting

### Files not uploading
- Check GS_* environment variables are set correctly
- Verify bucket is public (Storage Object Viewer role)
- Check service account has Storage Admin role

### Static files not loading
- Run `python manage.py collectstatic` locally and commit
- Check STATIC_URL in settings

### Database errors
- Check DATABASE_URL is correct in Vercel env vars
- Run migrations: `python manage.py migrate --settings=config.settings.vercel`

### CSRF errors
- Add your Vercel URL to CSRF_TRUSTED_ORIGINS

---

## Alternative: If You Don't Want Google Cloud

You can use these alternatives for file storage:
1. **Cloudinary** - Free 25GB (https://cloudinary.com)
2. **AWS S3** - Free 5GB for 12 months
3. **Dropbox API** - Free 2GB

But Google Cloud Storage (15GB free) is the best option since you already have a Gmail account!
