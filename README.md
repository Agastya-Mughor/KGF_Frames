Certainly! Here's a more detailed and comprehensive `README.md` for your Twitter Frame Bot project. This version is tailored to beginners or users with little to no knowledge of the project, providing them with a step-by-step guide to cloning and setting up their own version of the bot.

---

# Twitter Frame Bot Setup Guide

Welcome to the **Twitter Frame Bot** project! This guide will help you set up a Twitter bot that automatically tweets frames from a movie at regular intervals. You can easily customize this bot to use your own movie file and deploy it on Google Cloud Platform (GCP).

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Step-by-Step Setup](#step-by-step-setup)
   - [Clone the Repository](#clone-the-repository)
   - [Install Required Software](#install-required-software)
4. [Extract Frames from Your Movie](#extract-frames-from-your-movie)
5. [Configure the Project](#configure-the-project)
6. [Deploy to Google Cloud Platform (GCP)](#deploy-to-google-cloud-platform-gcp)
7. [Set Up the Bot to Run as a Service](#set-up-the-bot-to-run-as-a-service)
8. [Manage the Bot](#manage-the-bot)
9. [Troubleshooting and Tips](#troubleshooting-and-tips)
10. [Conclusion](#conclusion)

## Introduction

The **Twitter Frame Bot** is a Python-based script designed to automatically post frames extracted from a movie to a Twitter account at regular intervals. This project is perfect for sharing moments from your favorite films or creating an engaging Twitter feed.

## Requirements

Before you start, make sure you have the following:

- **GitHub Account**: To clone the repository and manage code versions.
- **Google Cloud Platform (GCP) Account**: For hosting the bot in a virtual machine.
- **Twitter Developer Account**: To create a Twitter app and obtain API keys.
- **A Movie File**: The movie from which you want to extract frames (e.g., `.mp4`, `.mkv`).
- **Basic Command Line Knowledge**: Understanding how to run commands in a terminal or command prompt.
- **FFmpeg**: For extracting frames from the movie file.
- **Python 3.9 or later**: The programming language used for the bot.
- **Internet Access**: To install necessary software and access APIs.

## Step-by-Step Setup

### Clone the Repository

1. **Create a Local Directory**:

   Choose a location on your computer where you want to store the bot files.

   ```bash
   mkdir TwitterBot
   cd TwitterBot
   ```

2. **Clone the GitHub Repository**:

   Open your terminal (Mac/Linux) or command prompt (Windows), navigate to the directory you created, and clone the repository:

   ```bash
   git clone https://github.com/Agastya-Mughor/KGF_Frames.git
   cd KGF_Frames
   ```

### Install Required Software

1. **Install Python and Pip**:

   - Download Python from the [official website](https://www.python.org/downloads/) and install it.
   - Make sure to check the option to add Python to your PATH during installation.

2. **Install Required Python Libraries**:

   Navigate to the directory where you cloned the repository and install the required Python libraries:

   ```bash
   pip install -r requirements.txt
   ```

   This command reads the `requirements.txt` file and installs all necessary libraries such as `tweepy`, `tenacity`, and others.

3. **Install FFmpeg**:

   FFmpeg is a tool for processing video and audio files.

   - **Windows**: Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html). Follow the instructions to add FFmpeg to your system PATH.
   - **Mac/Linux**: Install using a package manager:

   ```bash
   # Mac
   brew install ffmpeg

   # Linux
   sudo apt update
   sudo apt install ffmpeg -y
   ```

## Extract Frames from Your Movie

1. **Extract Frames Using FFmpeg**:

   Use FFmpeg to extract frames from your movie file. This command extracts 1 frame per second from your movie and saves them in a folder named `frames`.

   ```bash
   ffmpeg -i your_movie.mp4 -vf "fps=1" frames/frame_%04d.png
   ```

   - Replace `your_movie.mp4` with the path to your movie file.
   - This command creates a directory named `frames` and stores the extracted frames as PNG images.

2. **Organize Frames into Batches**:

   If your movie has many frames, consider organizing them into batches (e.g., `batch_1`, `batch_2`, etc.). Each batch can contain a maximum of 1000 images for easier management.

   ```bash
   mkdir frames_1
   mkdir frames_1/batch_1
   mkdir frames_1/batch_2
   # Move the first 1000 frames to batch_1, the next 1000 to batch_2, etc.
   ```

## Configure the Project

1. **Set Up Your Twitter Developer Account**:

   - Go to the [Twitter Developer Portal](https://developer.twitter.com/).
   - Create a new project and an app within the project.
   - Obtain your **API Key**, **API Key Secret**, **Access Token**, and **Access Token Secret**.

2. **Create a `.env` File**:

   The `.env` file stores your API keys and configuration settings securely. Create a `.env` file in the root directory of your project with the following content:

   ```bash
   # Twitter API Credentials
   API_KEY=your_twitter_api_key            # Replace with your actual API key
   API_KEY_SECRET=your_twitter_api_key_secret  # Replace with your actual API key secret
   ACCESS_TOKEN=your_twitter_access_token  # Replace with your actual access token
   ACCESS_TOKEN_SECRET=your_twitter_access_token_secret  # Replace with your actual access token secret

   # Email Configuration (Optional)
   EMAIL_ENABLED=True
   RECIPIENT_EMAIL=your_email@example.com  # Replace with your email
   MAILGUN_API_KEY=your_mailgun_api_key    # Replace with your Mailgun API key
   MAILGUN_DOMAIN=your_mailgun_domain      # Replace with your Mailgun domain

   # Frame Configuration
   FRAMES_DIR_1=frames_1
   FRAMES_DIR_2=frames_2
   HASHTAGS="#YourHashtag\n#AnotherHashtag"

   RESET_START=False
   ```


## Deploy to Google Cloud Platform (GCP)

1. **Install Google Cloud SDK**:

   Download and install the Google Cloud SDK from [here](https://cloud.google.com/sdk/docs/install). Initialize it by running:

   ```bash
   gcloud init
   ```

2. **Enable Required Google Cloud Services**:

   To use Compute Engine (GCP’s VM service), enable the necessary services:

   ```bash
   gcloud services enable compute.googleapis.com iap.googleapis.com
   ```

3. **Create a VM Instance**:

   Create a VM instance to host your bot:

   ```bash
   gcloud compute instances create twitter-bot-vm \
     --zone=us-central1-a \
     --machine-type=e2-micro \
     --image-family=debian-11 \
     --image-project=debian-cloud \
     --boot-disk-size=10GB \
     --boot-disk-type=pd-standard \
     --tags=http-server,https-server
   ```

   This command creates a new VM instance named `twitter-bot-vm` in the `us-central1-a` zone.

4. **Generate and Add SSH Keys**:

   Generate SSH keys on your local machine to access the VM securely:

   ```bash
   ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa
   ```

   Add the SSH public key to your GCP project:

   ```bash
   gcloud compute project-info add-metadata --metadata-from-file ssh-keys=~/.ssh/id_rsa.pub
   ```

5. **SSH into the VM**:

   Connect to your VM instance:

   ```bash
   gcloud compute ssh twitter-bot-vm --zone=us-central1-a
   ```

6. **Set Up the Environment on the VM**:

   Update and install necessary software:

   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install python3 python3-pip python3.9 python3.9-dev build-essential git -y
   ```

7. **Clone Your Repository on the VM**:

   Clone your GitHub repository to the VM:

   ```bash
   git clone https://github.com/your-username/KGF_Frames.git
   cd KGF_Frames
   pip3 install -r requirements.txt
   ```

## Set Up the Bot to Run as a Service

1. **Create a Systemd Service File**:

   Create a service file to manage the bot as a background service:

   ```bash
   sudo nano /etc/systemd/system/twitter-bot.service
   ```

   Add the following content (replace `your_vm_user` with your VM username):

   ```ini
   [Unit]
   Description=Twitter Bot Service
   After=network.target

   [Service]
   User=your_vm_user
   Working

Directory=/home/your_vm_user/KGF_Frames
   ExecStart=/usr/bin/python3 /home/your_vm_user/KGF_Frames/main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and Start the Service**:

   Enable and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable twitter-bot
   sudo systemctl start twitter-bot
   sudo systemctl status twitter-bot
   ```

   These commands will start the bot and ensure it runs whenever the VM starts.

## Manage the Bot

1. **Check the Bot Status**:

   To check if the bot is running correctly:

   ```bash
   sudo systemctl status twitter-bot
   ```

2. **Stop the Bot**:

   To stop the bot:

   ```bash
   sudo systemctl stop twitter-bot
   ```

3. **View Logs**:

   To view the bot's service logs:

   ```bash
   sudo journalctl -u twitter-bot
   ```

   To view logs in real-time:

   ```bash
   sudo journalctl -u twitter-bot -f
   ```

## Troubleshooting and Tips

1. **API Rate Limits**:

   - Be aware of Twitter's API rate limits. Make sure your bot doesn't exceed these limits to avoid temporary bans.

2. **Error Handling**:

   - The bot includes basic error handling and retry logic. Review the logs if you encounter issues.

3. **Updating the Bot**:

   - To update the bot, SSH into your VM, pull the latest changes from GitHub, and restart the service.

   ```bash
   git pull origin main
   sudo systemctl restart twitter-bot
   ```

## Conclusion

Congratulations! You have successfully set up and deployed your own instance of the **Twitter Frame Bot**. You can now tweet frames from your favorite movie at regular intervals. Customize the bot further to suit your needs, and have fun sharing your favorite movie moments on Twitter!

If you encounter any issues or have questions, feel free to open an issue on the GitHub repository.

---

