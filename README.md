# README.md

## Overview

This application provides a comprehensive analysis of your Garmin Connect data. It utilizes the official Garmin API to collect information about your body battery level, sleep analysis, and stress level over a defined period of time (default is the past 30 days).

The collected data is then processed, analysed, and summarised, responses from the OpenAI API is used to provide specific recommendations and insights, based on your sleep and stress levels. The program will provide a correlation between your maintained energy balance, stress levels, and quality of sleep. Finally, the program generates HTML reports and saves visualized data plots.

## Installation

First, clone the repository to your local machine.

```bash
git clone https://github.com/user/repo.git
```
Navigate to the cloned repository.

```bash
cd your_project_directory
```
Before you install the required packages, it is recommended to create a virtual environment.

```bash
# Linux/macOS
python3 -m venv venv

# Windows
py -m venv venv
```
Activate the virtual environment.

```bash
# Linux/macOS
source venv/bin/activate

# Windows
.\venv\Scripts\activate
```
Then, use `pip` to install the required libraries using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```
## Environment Variables

You have to configure the below environment variables.

```bash
export EMAIL=<Your Garmin Connect email address>
export PASSWORD=<Your Garmin Connect password>
export OPENAI_API_KEY=<Your OpenAI API Key>
```
You can also configure these variables to specify tokenstore directories.

```bash
export GARMINTOKENS=<Tokenstore directory>
export GARMINTOKENS_BASE64=<Tokenstore base64 directory>
```

## Using the dotenv file to set variables

The application uses environment variables to manage and secure sensitive
data that is needed at runtime. For smooth usage, the app looks for a  .env
file at the root of the project, and this file should follow the format of
the  env.sample  file provided.

To set up your environment variables:

1. Locate the  env.sample  file at the root of the project.
2. Copy the contents of this file into a new file named  .env .

Here's an example of what the contents of the  .env  file should look like:

# Garmin Connect API Credentials
GARMINEMAIL=your_garmin_email
GARMINPASSWORD=your_garmin_password
OPENAI_API_KEY=your_openai_api_key

# Token Storage Locations
GARMINTOKENS=~/.garminconnect
GARMINTOKENS_BASE64=~/.garminconnect_base64

# SMTP Configuration for Email Reporting
SMTP_SERVER=your_smtp_server
SMTP_PORT=587
FROM_ADDRESS=your_from_address
SMTP_TO=your_to_address
SMTP_USER=your_smtp_user
SMTP_PASSWORD=your_smtp_password

Copy the above and replace  your_garmin_email ,  your_garmin_password ,
your_openai_api_key ,  your_smtp_server ,  your_from_address ,
your_to_address ,  your_smtp_user , and  your_smtp_password  with your
actual data.

Once you've got your  .env  file set up with your own values, the
application will be able to access these values and use them at runtime.

Remember not to add the  .env  file to your version control system, as this
can potentially expose your confidential data. Keep it safe and untracked.

## Usage

This application is a command line program. Once installed and environment variables are configured, you can use it directly in your terminal.

Use the following command to start the application:

```bash
python3 main.py
```
After successful run, you can find an HTML report named 'energy_report.html' and plots ('charged_vs_drained_plot.png', 'stress_level.png', 'sleep_statistics.png') in your project directory. Open 'energy_report.html' with your preferred browser to view the report.

''Note: You will be required to authenticate your Garmin Connect account on the first run of the application, all tokens will be stored for future use.''

