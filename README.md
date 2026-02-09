# Cisia Alerts

## Project Description

Cisia Alerts is a powerful alert management system designed to monitor various environmental conditions and notify users of critical status changes. The application collects data from different sources, processes it, and sends timely alerts to keep users informed and proactive.

## Features

- Real-time monitoring of environmental conditions
- Customizable alert thresholds
- Notifications via email/SMS
- User-friendly dashboard for tracking alerts and data
- Integration with various data sources

## Installation Instructions

To set up the Cisai Alerts application locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/navdeepg053-cpu/Cisia_alerts.git
   ```
   
2. Navigate to the project directory:
   ```bash
   cd Cisai_alerts
   ```

3. Install the required dependencies:
   ```bash
   npm install
   ```

4. Set up environment variables (see Environment Setup).

## Deployment Guide for Render.com

1. Log in to your Render account and create a new Web Service.
2. Connect your GitHub repository to Render.
3. Choose the branch you want to deploy.
4. Set up environment variables in the Render dashboard according to your application needs.
5. Click "Deploy" and Render will build and host your application.

## Environment Setup

Make sure to create a `.env` file in the root directory of your project. Here are the required variables:

```
DATABASE_URL=your_database_url
EMAIL_SERVICE=your_email_service
EMAIL_USERNAME=your_email_username
EMAIL_PASSWORD=your_email_password
ALERT_THRESHOLD=your_alert_threshold
```

## Usage Commands

To run the application locally, use the following command:

```bash
npm start
```

After starting the application, access it via `http://localhost:3000`.

## Troubleshooting

If you encounter issues during installation or running the application, consider the following:

- Ensure that Node.js and npm are installed and updated.
- Check the database connection string for accuracy.
- Review the logs for any error messages to identify the problem.

## Technical Details

- **Tech Stack:** Node.js, Express, MongoDB, React
- **Custom Libraries:** 
  - Axios for API requests
  - Nodemailer for email notifications
- **Testing Framework:** Jest for unit and integration testing

For any further inquiries or contributions, please refer to the `CONTRIBUTING.md` file or open an issue on GitHub.