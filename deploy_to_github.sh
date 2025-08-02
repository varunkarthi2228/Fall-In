#!/bin/bash

# 🚀 GitHub Deployment Script for Fall In
# This script helps you deploy your Fall In app to GitHub

echo "💕 Fall In - GitHub Deployment Script"
echo "====================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please run 'git init' first."
    exit 1
fi

# Get GitHub username
read -p "Enter your GitHub username: " github_username

if [ -z "$github_username" ]; then
    echo "❌ GitHub username is required!"
    exit 1
fi

echo ""
echo "📋 Steps to deploy to GitHub:"
echo "=============================="
echo ""
echo "1️⃣  Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Repository name: fall-in"
echo "   - Make it Public"
echo "   - Don't initialize with README"
echo "   - Click 'Create repository'"
echo ""
echo "2️⃣  Run these commands:"
echo "   git remote add origin https://github.com/$github_username/fall-in.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3️⃣  Your repository will be available at:"
echo "   https://github.com/$github_username/fall-in"
echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📚 Next steps:"
echo "   - Check out DEPLOYMENT.md for hosting options"
echo "   - Consider deploying to Railway, PythonAnywhere, or Heroku"
echo "   - Set up environment variables on your hosting platform"
echo ""
echo "🔗 Useful links:"
echo "   - Railway: https://railway.app"
echo "   - PythonAnywhere: https://www.pythonanywhere.com"
echo "   - Heroku: https://heroku.com" 