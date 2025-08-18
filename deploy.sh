#!/bin/bash

# PostgreSQL-based deployment script for Google Cloud
# This script builds and deploys the application using PostgreSQL

set -e

echo "🚀 Starting PostgreSQL-based deployment..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No project ID set. Please run 'gcloud config set project PROJECT_ID' first."
    exit 1
fi

echo "📋 Project ID: $PROJECT_ID"

# Check if we're in the right directory
if [ ! -f "Dockerfile" ] || [ ! -f "cloudbuild.yaml" ]; then
    echo "❌ Error: Please run this script from the root directory containing Dockerfile and cloudbuild.yaml"
    exit 1
fi

# Build and deploy using Cloud Build
echo "🔨 Building and deploying with Cloud Build..."
gcloud builds submit --config cloudbuild.yaml

echo "✅ Deployment completed successfully!"
echo ""
echo " Your application should now be available at:"
echo "   https://data-assistant-$(gcloud config get-value run/region)-$(gcloud config get-value project).run.app"
echo ""
echo " To view logs and monitor:"
echo "   gcloud logging read 'resource.type=cloud_run_revision' --limit=50"
echo ""
echo " To update the application, simply run this script again."
