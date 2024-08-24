# Twitter Frame Bot

## Overview

The **Twitter Frame Bot** is designed to post frames from the KGF movie on Twitter. The bot extracts and tweets one frame every 30 minutes at a rate of 1 frame per second (fps). 

## Features

- **Regular Posting**: Tweets a single frame from KGF every 30 minutes.
- **Frame Handling**: Automatically manages and transitions between different batches of frames.
- **Error Handling**: Includes retry mechanisms for failed tweet attempts and frame retrieval.
- **Email Notifications**: Sends email alerts for critical errors and upon completion of the movie processing.
- **Configurable**: Adjusts settings such as tweet delay and frame directories through environment variables and a configuration file.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Twitter Developer account with API credentials
- Mailgun account for email notifications
- Required Python packages listed in `requirements.txt`

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/twitter-frame-bot.git
   cd twitter-frame-bot
   ```

2. **Set Up Environment Variables**

   Create a `.env` file in the root directory with the following content:

   ```env
   API_KEY=your_twitter_api_key
   API_KEY_SECRET=your_twitter_api_key_secret
   ACCESS_TOKEN=your_twitter_access_token
   ACCESS_SECRET=your_twitter_access_secret
   MAILGUN_API_KEY=your_mailgun_api_key
   MAILGUN_DOMAIN=your_mailgun_domain
   RECIPIENT_EMAIL=your_email@example.com
   EMAIL_ENABLED=True
   RESET_START=False
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Frame Directories**

   Ensure your frame directories are set up according to the following format:

   ```
   frames_1/
       batch_1/
       batch_2/
       ...
   frames_2/
       batch_1/
       batch_2/
       ...
   ```

5. **Create Configuration File**

   Create a `config.yaml` file with the following default settings:

   ```yaml
   tweetDelay: 30
   currentMovie: 1
   currentFrame_1: 1
   currentFrame_2: 1
   ```

### Running the Bot

Run the bot using:

```bash
python main.py
```

### Configuration

- **Tweet Delay**: Time interval between tweets (in minutes). Configured via `tweetDelay` in `config.yaml`.
- **Frame Directory**: Path to the directory containing movie frames. Configured via environment variables `FRAMES_DIR_1`, `FRAMES_DIR_2`, etc.
- **Hashtags**: Set in the environment variable `HASHTAGS`.

### Email Notifications

- Enable or disable email notifications using the `EMAIL_ENABLED` variable in the `.env` file.
- Ensure Mailgun credentials are correctly set for sending emails.

## Troubleshooting

- **Frame Not Found**: Check the frame directories and ensure frames are named correctly.
- **Rate Limits**: If you encounter rate limits, the bot will wait and retry based on the error response.
- **Configuration Issues**: Ensure all environment variables and configuration settings are properly set.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or issues, please contact [your_email@example.com](mailto:your_email@example.com).
