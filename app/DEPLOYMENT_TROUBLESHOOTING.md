# Deployment Troubleshooting Guide

## Common Railway Deployment Issues & Fixes

### Issue 1: "Failed to get private network endpoint"
**What it means:** Railway is having trouble setting up internal networking for your app.

**Fix:**
1. **Wait 2-3 minutes** - this often resolves itself
2. **Check the deployment logs** in Railway
3. **Redeploy** by clicking "Deploy" again

### Issue 2: Build Failures
**Check the build logs for these common errors:**

#### Import Errors
```
ModuleNotFoundError: No module named 'database'
```
**Fix:** ✅ Already fixed - removed relative imports

#### Database Connection Errors
```
OperationalError: could not connect to server
```
**Fix:** 
1. Make sure you have a PostgreSQL database created in Railway
2. Check that `DATABASE_URL` environment variable is set correctly

#### Port Binding Issues
```
OSError: [Errno 98] Address already in use
```
**Fix:** ✅ Already fixed - using `$PORT` environment variable

### Issue 3: App Won't Start
**Check startup logs for:**
- Missing dependencies
- Database initialization failures
- Template loading errors

## Quick Fix Checklist

Before redeploying, ensure:

- [ ] All files are committed to GitHub
- [ ] `requirements.txt` is up to date
- [ ] `railway.json` is present
- [ ] Database is created in Railway
- [ ] `DATABASE_URL` environment variable is set

## Redeployment Steps

1. **Fix any code issues** (✅ Already done)
2. **Commit and push** changes to GitHub
3. **In Railway:** Click "Deploy" button
4. **Wait 2-3 minutes** for deployment to complete
5. **Check logs** if issues persist

## Environment Variables to Set

In Railway, make sure you have:

```
DATABASE_URL=postgresql://... (from your database settings)
ENVIRONMENT=production
```

## Still Having Issues?

1. **Check Railway status page** - sometimes it's a platform issue
2. **Try Render.com** as an alternative (also free)
3. **Check GitHub repository** - ensure all files are committed

## Success Indicators

Your app is successfully deployed when:
- ✅ Build status shows "Deployed"
- ✅ You can access your app URL
- ✅ Health check endpoint `/health` returns success
- ✅ No red error messages in Railway dashboard
