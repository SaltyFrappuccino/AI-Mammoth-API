# Deployment Guide for AI Mammoth API

This document outlines different deployment options for the AI Mammoth API application.

## Vercel Deployment (Lightweight Version)

Due to Vercel's serverless function size limit of 250MB, we've created a lightweight version of the API that can be deployed to Vercel.

### Steps to Deploy on Vercel

1. Make sure you have the Vercel CLI installed:
   ```
   npm install -g vercel
   ```

2. Deploy using the provided configuration:
   ```
   vercel
   ```

3. The lightweight deployment includes:
   - A `/analyze` endpoint that returns a request ID (but doesn't perform actual analysis)
   - A `/api/health` endpoint to verify the API is running

### Limitations of Vercel Deployment

- The Vercel deployment does not include the full analysis capabilities
- It's meant to be used as a frontend or proxy to a full deployment elsewhere

## Full Docker Deployment

For the complete AI Mammoth API with all features, use the Docker deployment.

### Steps to Deploy with Docker

1. Build the Docker image:
   ```
   docker build -t ai-mammoth-api .
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 ai-mammoth-api
   ```

3. The API will be available at http://localhost:8080

### Docker Deployment on Cloud Providers

You can deploy the Docker container on various cloud providers:

#### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-mammoth-api

# Deploy to Cloud Run
gcloud run deploy ai-mammoth-api --image gcr.io/YOUR_PROJECT_ID/ai-mammoth-api --platform managed
```

#### Azure Container Instances

```bash
# Create a resource group
az group create --name myResourceGroup --location eastus

# Create a container registry
az acr create --resource-group myResourceGroup --name myContainerRegistry --sku Basic

# Build and push to Azure Container Registry
az acr build --registry myContainerRegistry --image ai-mammoth-api:latest .

# Deploy to Azure Container Instances
az container create --resource-group myResourceGroup --name ai-mammoth-api --image myContainerRegistry.azurecr.io/ai-mammoth-api:latest --dns-name-label ai-mammoth-api --ports 8080
```

#### AWS Elastic Container Service

1. Create an ECR repository
2. Push your Docker image to ECR
3. Deploy using ECS or Fargate

## Hybrid Deployment Approach

For a more cost-effective solution, you can use a hybrid approach:

1. Deploy the lightweight version on Vercel for your frontend/API gateway
2. Deploy the full Docker version on a more appropriate platform (AWS, GCP, Azure)
3. Configure the Vercel deployment to forward analysis requests to your full deployment

This approach gives you the benefits of Vercel's global CDN while handling the resource-intensive operations on a more suitable platform. 