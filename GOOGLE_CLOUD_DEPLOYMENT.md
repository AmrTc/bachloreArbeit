# Google Cloud Deployment Guide - PostgreSQL Version

This guide explains how to deploy the Data Assistant application to Google Cloud using PostgreSQL as the database backend.

## 🗄️ Database Architecture

The application now uses **PostgreSQL** instead of SQLite for better scalability and cloud compatibility:

- **Database**: Google Cloud SQL (PostgreSQL 17)
- **Host**: 34.59.248.159
- **Port**: 5432
- **Database Name**: superstore
- **User**: postgres
- **SSL Mode**: require

## 🚀 Prerequisites

1. **Google Cloud Account**: Active Google Cloud project
2. **gcloud CLI**: Installed and authenticated
3. **PostgreSQL Instance**: Running Google Cloud SQL instance
4. **API Keys**: Anthropic API key for AI functionality

## 📋 Setup Steps

### 1. Configure Google Cloud Project

```bash
# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

### 2. Set Up Secrets

Run the secrets setup script:

```bash
chmod +x setup_secrets.sh
./setup_secrets.sh
```

This will create:
- `anthropic-api-key`: Your Anthropic API key
- `postgres-host`: PostgreSQL host address
- `postgres-database`: Database name
- `postgres-user`: Database username
- `postgres-password`: Database password
- `postgres-port`: Database port
- `postgres-sslmode`: SSL mode

### 3. Configure PostgreSQL Connection

The application automatically uses these environment variables:

```bash
export PG_HOST="34.59.248.159"
export PG_PORT="5432"
export PG_DATABASE="superstore"
export PG_USER="postgres"
export PG_PASSWORD="your_password"
export PG_SSLMODE="require"
export PG_CONNECT_TIMEOUT="30"
```

### 4. Deploy the Application

Use the deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

Or manually with Cloud Build:

```bash
gcloud builds submit --config cloudbuild.yaml
```

## 🔧 Configuration Files

### Dockerfile
- Uses Python 3.12 slim image
- Installs PostgreSQL client libraries (`libpq-dev`)
- Copies application code to `/app` directory
- Runs as non-root user for security

### cloudbuild.yaml
- Builds Docker image from root directory
- Pushes to Google Container Registry
- Tags with commit SHA and 'latest'

### cloudbuild.secrets.yaml
- Includes secret management
- Sets PostgreSQL environment variables
- Deploys to Cloud Run with proper configuration

## 🌐 Deployment Options

### Option 1: Basic Deployment
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Option 2: Deployment with Secrets
```bash
gcloud builds submit --config cloudbuild.secrets.yaml
```

### Option 3: Manual Cloud Run Deployment
```bash
gcloud run deploy data-assistant \
    --image gcr.io/YOUR_PROJECT_ID/data-assistant:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --set-env-vars PG_HOST=34.59.248.159,PG_PORT=5432,PG_DATABASE=superstore,PG_USER=postgres,PG_SSLMODE=require
```

## 🔍 Monitoring and Logs

### View Application Logs
```bash
gcloud logging read 'resource.type=cloud_run_revision' --limit=50
```

### Monitor Cloud Run Service
```bash
gcloud run services describe data-assistant --region us-central1
```

### Check Build Status
```bash
gcloud builds list --limit=10
```

## 🚨 Troubleshooting

### Common Issues

1. **PostgreSQL Connection Failed**
   - Verify the instance is running
   - Check firewall rules allow connections
   - Ensure SSL mode is set to 'require'

2. **Build Failures**
   - Check Dockerfile syntax
   - Verify all required files are present
   - Check Cloud Build logs for detailed errors

3. **Runtime Errors**
   - Verify all secrets are properly set
   - Check environment variables
   - Review application logs

### Debug Commands

```bash
# Test PostgreSQL connection
gcloud sql connect superstore-instanz --user=postgres

# Check secrets
gcloud secrets list

# View build logs
gcloud builds log BUILD_ID

# Test Cloud Run service
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
     https://data-assistant-us-central1-YOUR_PROJECT_ID.run.app
```

## 🔄 Updating the Application

To update the application:

1. **Commit your changes** to Git
2. **Run the deployment script** again:
   ```bash
   ./deploy.sh
   ```

The script will:
- Build a new Docker image
- Push to Container Registry
- Deploy to Cloud Run
- Update the service automatically

## 📊 Performance Considerations

### PostgreSQL Optimization
- Use connection pooling for high traffic
- Implement proper indexing on frequently queried columns
- Monitor query performance with `EXPLAIN ANALYZE`

### Cloud Run Optimization
- Set appropriate memory and CPU limits
- Use concurrency settings for better resource utilization
- Monitor cold start times

## 🔐 Security Best Practices

1. **Secrets Management**
   - Never commit secrets to version control
   - Use Google Secret Manager for sensitive data
   - Rotate secrets regularly

2. **Network Security**
   - Use SSL connections to PostgreSQL
   - Restrict database access to Cloud Run IPs
   - Implement proper IAM roles

3. **Application Security**
   - Run containers as non-root users
   - Keep dependencies updated
   - Implement proper authentication

## 📚 Additional Resources

- [Google Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)
- [Secret Manager Guide](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Documentation](https://cloud.google.com/cloud-build/docs)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Cloud Build and Cloud Run logs
3. Verify PostgreSQL connection and configuration
4. Ensure all required APIs are enabled
5. Check IAM permissions for your service account

---

**Note**: This deployment uses PostgreSQL for production scalability. The application automatically handles database connections and migrations.
