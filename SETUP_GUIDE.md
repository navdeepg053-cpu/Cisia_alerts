# SETUP GUIDE

## Deployment on Render.com with MongoDB Atlas

### Prerequisites

1. **Create a Render Account**: Sign up at [Render.com](https://render.com) if you don't have an account.
2. **MongoDB Atlas Account**: Sign up for a MongoDB Atlas account at [mongodb.com](https://www.mongodb.com/cloud/atlas).

### Steps for Setup

#### 1. Create a MongoDB Atlas Cluster

- Go to your MongoDB Atlas dashboard.
- Click on "Build a Cluster."
- Follow the setup instructions to create a free cluster.
- Once created, navigate to the "Database Access" section and create a new user with read and write access.
- Under "Network Access," allow access from the Render IP addresses.

#### 2. Obtain Connection String

- After setting up the cluster, go to "Clusters" and click on "Connect".
- Select "Connect your application" and copy the connection string.
- Replace `<password>` with the password for the user you created earlier.

#### 3. Set Up Your Render Web Service

- Log in to your Render account.
- Click on "New" and select "Web Service."
- Connect your GitHub account if prompted.
- Select the `navdeepg053-cpu/Cisia_alerts` repository.
- Configure the service settings:
  - **Branch**: Specify the branch you want to deploy.
  - **Build Command**: Add the build command (e.g., `npm install`).
  - **Start Command**: Add the start command (e.g., `npm start`).

#### 4. Environment Variables

- Under the "Environment" section, add these variables:
  - `MONGODB_URI`: Your MongoDB connection string.
  - Any other variables required by your application.

#### 5. Deploy Your Application

- Click "Create Web Service."
- Render will start building and deploying your application.

#### 6. Access Your Application

- After the deployment finishes, Render will provide a URL to access your application.

### Additional Resources

- [Render Documentation](https://render.com/docs)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)