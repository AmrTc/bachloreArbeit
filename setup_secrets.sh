#!/bin/bash

# PostgreSQL-based secrets setup script for Google Cloud
# This script sets up the Anthropic API key and PostgreSQL configuration in Google Secret Manager

set -e

echo "🔐 Setting up PostgreSQL-based secrets for Google Cloud..."

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

# Enable Secret Manager API
echo "🔧 Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Create the Anthropic API key secret
echo "🔑 Creating Anthropic API key secret..."
echo "Please enter your Anthropic API key:"
read -s ANTHROPIC_API_KEY

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: API key cannot be empty"
    exit 1
fi

# Create the secret
echo "$ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key --data-file=-

echo "✅ Anthropic API key secret created successfully!"

# Create PostgreSQL configuration secrets
echo "🗄️ Creating PostgreSQL configuration secrets..."

# Create PostgreSQL host secret
echo "34.59.248.159" | gcloud secrets create postgres-host --data-file=-
echo "✅ PostgreSQL host secret created"

# Create PostgreSQL database secret
echo "superstore" | gcloud secrets create postgres-database --data-file=-
echo "✅ PostgreSQL database secret created"

# Create PostgreSQL user secret
echo "postgres" | gcloud secrets create postgres-user --data-file=-
echo "✅ PostgreSQL user secret created"

# Create PostgreSQL password secret
echo "Please enter your PostgreSQL password:"
read -s POSTGRES_PASSWORD

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "❌ Error: PostgreSQL password cannot be empty"
    exit 1
fi

echo "$POSTGRES_PASSWORD" | gcloud secrets create postgres-password --data-file=-
echo "✅ PostgreSQL password secret created"

# Create PostgreSQL port secret
echo "5432" | gcloud secrets create postgres-port --data-file=-
echo "✅ PostgreSQL port secret created"

# Create PostgreSQL SSL mode secret
echo "require" | gcloud secrets create postgres-sslmode --data-file=-
echo "✅ PostgreSQL SSL mode secret created"

echo ""
echo "   All secrets created successfully!"
echo ""
echo "   Created secrets:"
echo "   - anthropic-api-key"
echo "   - postgres-host"
echo "   - postgres-database"
echo "   - postgres-user"
echo "   - postgres-password"
echo "   - postgres-port"
echo "   - postgres-sslmode"
echo ""
echo "🔧 To use these secrets in Cloud Run, reference them like:"
echo "   --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest"
echo "   --set-secrets PG_PASSWORD=postgres-password:latest"
echo ""
echo "📚 For more information, see:"
echo "   https://cloud.google.com/run/docs/configuring/secrets"
