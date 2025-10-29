#!/bin/bash

# GitHub Repository Push Script
# Run this script in the AI-Content-Automation directory

echo "🚀 Pushing Automated Content Creator to GitHub..."

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the AI-Content-Automation directory"
    exit 1
fi

# Add README and commit
echo "📖 Adding README and creating commit..."
git add README.md
git commit -m "📖 Add comprehensive README with usage instructions"

# Try to push (will prompt for credentials)
echo "📤 Pushing to GitHub..."
echo "Repository: https://github.com/jsimoes215/AI-Content-Automation.git"
echo ""
echo "You'll be prompted for credentials. Use:"
echo "• Username: jsimoes215"  
echo "• Password: [Your Personal Access Token]"
echo ""

git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🎉 Your repository is now live at:"
    echo "https://github.com/jsimoes215/AI-Content-Automation"
else
    echo "❌ Push failed. You can try manually:"
    echo "git push origin main"
fi