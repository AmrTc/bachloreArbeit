#!/bin/bash

# Script to securely store Anthropic API Key in Google Secret Manager
PROJECT_ID="your-project-id"
SECRET_NAME="anthropic-api-key"

echo "🔐 Setting up secure storage for Anthropic API Key..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set the project
echo "📋 Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable Secret Manager API
echo "🔧 Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Create the secret
echo "🔑 Creating secret: $SECRET_NAME"
echo "Please enter your Anthropic API Key (it will be hidden):"
read -s API_KEY

# Create the secret
echo "$API_KEY" | gcloud secrets create $SECRET_NAME --data-file=-

echo "✅ Secret created successfully!"
echo "📝 To access this secret in your application, use:"
echo "gcloud secrets versions access latest --secret=$SECRET_NAME"

# Grant access to Cloud Run service account
echo "🔓 Granting access to Cloud Run service account..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

echo "✅ Access granted to Cloud Run service account!"
