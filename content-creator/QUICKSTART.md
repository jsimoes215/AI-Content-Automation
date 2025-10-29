# Quick Start Guide - AI Content Automation System

## Get Started in 5 Minutes

### Step 1: Start the System
```bash
cd /workspace/content-creator
bash start.sh
```

Wait for both servers to start (about 10 seconds).

### Step 2: Access the Interface
Open your browser and go to: **http://localhost:5173**

### Step 3: Create Your First Project

1. Click **"New Project"** button on the Dashboard
2. Fill in the form:
   - **Video Idea**: "Create a tutorial on using AI for productivity"
   - **Target Audience**: "busy professionals"
   - **Tone**: "educational"
3. Click **"Create Project"**

### Step 4: Generate Script

1. Click on your project in the list
2. Click **"Generate Script"** button
3. Watch real-time progress in the "Generation Jobs" section
4. Script will be generated in about 30 seconds

### Step 5: Explore Features

- **Dashboard**: View overview and recent projects
- **Projects**: Manage all your content projects
- **Content Library**: Browse and reuse scenes
- **Analytics**: Track performance metrics

## Common Tasks

### Create a Project
1. Go to Projects page
2. Click "New Project"
3. Enter idea, audience, and tone
4. Click "Create Project"

### Generate Content
1. Open a project
2. Click "Generate Script"
3. Monitor progress in real-time
4. View results when complete

### Search Content Library
1. Go to Content Library
2. Enter tags (comma-separated)
3. Apply category filter
4. Click "Search"

### View Analytics
1. Go to Analytics page
2. Select timeframe
3. View charts and metrics

## Keyboard Shortcuts

- **Ctrl/Cmd + K**: Quick search (coming soon)
- **Ctrl/Cmd + N**: New project (coming soon)
- **Ctrl/Cmd + ,**: Settings (coming soon)

## Tips

1. **Use descriptive project names** - Makes finding projects easier
2. **Tag your scenes** - Better for searching and reuse
3. **Monitor progress** - Real-time updates show job status
4. **Check analytics** - Track what works best

## Need Help?

- **API Documentation**: http://localhost:8000/docs
- **System Documentation**: See SYSTEM_DOCUMENTATION.md
- **Full README**: See README_WEB_INTERFACE.md

## Stopping the System

Press **Ctrl+C** in the terminal where you ran `start.sh`

Or manually:
```bash
# Find processes
ps aux | grep uvicorn
ps aux | grep vite

# Kill them
kill <PID>
```

## Next Steps

- Explore the content library
- Generate multiple projects
- Check out the analytics dashboard
- Integrate with the AI pipeline

Happy creating!
