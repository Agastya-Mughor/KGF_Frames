import os
import sys
import logging
import traceback
import tweepy
import requests
import json
from datetime import timedelta
from dotenv import load_dotenv
from time import sleep
from logging.handlers import RotatingFileHandler

# Store the working directory
dir = os.path.abspath(os.path.dirname(__file__))

# Set up rotating log handler to limit log size
log_handler = RotatingFileHandler(f"{dir}/log.txt", maxBytes=5*1024*1024, backupCount=2)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

# Begin logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Add a line gap for every session in the logs
logger.info("\n" + "="*80 + "\nNew Session Started\n" + "="*80 + "\n")

logger.info("Every Frame In Order Twitter Bot started")

# Load environment variables from the .env file
load_dotenv()

# Access the environment variables
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_KEY_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Mailgun configuration
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
recipient_email = os.getenv("RECIPIENT_EMAIL")
email_enabled = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
reset_start = os.getenv("RESET_START", "False").lower() == "true"

# Validate environment variables
def validate_env_vars():
    missing_vars = []
    if not api_key: missing_vars.append("API_KEY")
    if not api_secret: missing_vars.append("API_KEY_SECRET")
    if not access_token: missing_vars.append("ACCESS_TOKEN")
    if not access_secret: missing_vars.append("ACCESS_TOKEN_SECRET")
    if not MAILGUN_API_KEY: missing_vars.append("MAILGUN_API_KEY")
    if not MAILGUN_DOMAIN: missing_vars.append("MAILGUN_DOMAIN")
    if not recipient_email: missing_vars.append("RECIPIENT_EMAIL")
    
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(f"Missing environment variables: {', '.join(missing_vars)}")

validate_env_vars()

# Function to send an email notification using Mailgun with exponential backoff
def send_email(subject, message):
    if email_enabled:
        retries = 0
        backoff = 30  # Initial backoff time in seconds
        max_retries = 5

        while retries < max_retries:
            try:
                response = requests.post(
                    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                    auth=("api", MAILGUN_API_KEY),
                    data={
                        "from": f"Twitter Bot <mailgun@{MAILGUN_DOMAIN}>",
                        "to": [recipient_email],
                        "subject": subject,
                        "text": message
                    }
                )
                response.raise_for_status()
                logger.info(f"Email sent: {subject}")
                return True
            except requests.exceptions.RequestException as e:
                if response.status_code == 429:
                    retries += 1
                    logger.error(f"Mailgun rate limit exceeded: {e}. Retrying in {backoff} seconds...")
                    sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to send email: {e}")
                    break
        return False

# Authenticating with Twitter
def authenticate_twitter():
    try:
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True, retry_count=3, retry_delay=120, retry_errors={503})
        client = tweepy.Client(consumer_key=api_key, consumer_secret=api_secret, access_token=access_token, access_token_secret=access_secret)
        return api, client
    except Exception as e:
        logger.error("Error during Twitter authentication")
        logger.exception(e)
        send_email("Twitter Bot Error", f"Error during Twitter authentication: {str(e)}")
        sys.exit("Twitter authentication failed")

api, client = authenticate_twitter()

# Function to save config data
def save_config(config_path, config_data):
    try:
        with open(config_path, 'w') as config_file:
            json.dump(config_data, config_file)
        logger.info("Configuration saved successfully.")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")

# Load configuration from external file
config_path = f"{dir}/config.json"
if os.path.exists(config_path):
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)
else:
    config_data = {
        'tweetDelay': '30',  # Number of seconds between each tweet
        'currentMovie': '1',  # Start with movie 1
        'currentFrame_1': '1',  # Current frame for movie 1
        'currentFrame_2': '1',  # Current frame for movie 2
    }

# If RESET_START is True, reset the state to start from movie 1
if reset_start:
    config_data['currentMovie'] = '1'
    config_data['currentFrame_1'] = '1'
    config_data['currentFrame_2'] = '1'
    logger.info("RESET_START is True. Resetting state to start from movie 1.")
    save_config(config_path, config_data)

# Number of seconds between tweets
tweetDelay = int(config_data['tweetDelay'])

# Path to frame directories
frame_dirs = {
    '1': "frames_1",
    '2': "frames_2"
}

# Function to get time remaining in a readable format
def get_time_remaining(sec):
    timedelta_str = str(timedelta(seconds=sec))
    x = timedelta_str.split(':')
    dh = x[0]
    m = x[1]
    s = x[2]
    logger.info(f"Time remaining: {dh} hours {m} minutes {s} seconds")

# Store traceback exception and print to console and log
def print_error():
    error = traceback.format_exc()
    logger.exception("An exception was thrown and the bot might have stopped posting!")
    logger.error(error)
    send_email("Twitter Bot Error", f"An exception occurred: {error}")

# Function to get total number of frames across all batches
def get_total_frames_in_movie(frame_path):
    total_frames = 0
    batch_folders = [folder for folder in os.listdir(frame_path) if folder.startswith('batch_')]
    for batch_folder in batch_folders:
        batch_path = os.path.join(frame_path, batch_folder)
        frames = [f for f in os.listdir(batch_path) if f.endswith('.jpg')]
        total_frames += len(frames)
    return total_frames

# Function to find the frame file in batches
def find_frame_in_batches(frame_path, frame_number):
    batch_folders = sorted([folder for folder in os.listdir(frame_path) if folder.startswith('batch_')])
    for batch_folder in batch_folders:
        batch_path = os.path.join(frame_path, batch_folder)
        frame_file = f"frame_{frame_number}.jpg"
        frame_full_path = os.path.join(batch_path, frame_file)
        if os.path.isfile(frame_full_path):
            return frame_full_path
    return None

# Function to tweet a frame with exponential backoff
def tweet_frame(full_tweet, media):
    retries = 0
    backoff = 30  # Initial backoff time in seconds
    max_retries = 5

    while retries < max_retries:
        try:
            client.create_tweet(text=full_tweet, media_ids=[media.media_id])
            logger.info("Tweet sent successfully.")
            return True
        except tweepy.TooManyRequests as e:
            retries += 1
            logger.error(f"Twitter rate limit exceeded: {e}. Retrying in {backoff} seconds...")
            sleep(backoff)
            backoff *= 2  # Exponential backoff
        except Exception as e:
            logger.error(f"Failed to send tweet: {e}")
            return False
    return False

# Function to process frames
def process_frames():
    while True:
        currentMovie = config_data.get('currentMovie', '1')
        frame_dir = frame_dirs.get(currentMovie)
        frame_path = f"{dir}/{frame_dir}"
        currentFrame = config_data.get(f'currentFrame_{currentMovie}', '1')

        logger.info(f"Processing Movie {currentMovie} - Current frame: {currentFrame}")

        try:
            totalFrames = get_total_frames_in_movie(frame_path)
            logger.info(f"Total number of frames in the movie: {totalFrames}")

            if int(currentFrame) > totalFrames:
                logger.info(f"All frames processed for Movie {currentMovie}.")
                next_movie_number = str(int(currentMovie) + 1)
                next_frame_dir = frame_dirs.get(next_movie_number)

                if next_frame_dir and os.path.exists(f"{dir}/{next_frame_dir}"):
                    config_data['currentMovie'] = next_movie_number
                    config_data[f'currentFrame_{next_movie_number}'] = '1'
                    logger.info(f"Switching to Movie {next_movie_number}")
                else:
                    logger.info("No more movies to process. Stopping the bot.")
                    send_email("Twitter Bot Completed", "The bot has successfully posted all frames from all movies.")
                    break
            else:
                frame_full_path = find_frame_in_batches(frame_path, currentFrame)

                if frame_full_path:
                    tweet_content = f"Frame {currentFrame} from Movie {currentMovie}"
                    logger.info(f"Tweeting: {tweet_content}")
                    media = api.media_upload(frame_full_path)
                    tweeted = tweet_frame(tweet_content, media)

                    if tweeted:
                        config_data[f'currentFrame_{currentMovie}'] = str(int(currentFrame) + 1)
                        save_config(config_path, config_data)
                        logger.info(f"Successfully tweeted frame {currentFrame}. Next frame: {int(currentFrame) + 1}")
                        get_time_remaining(tweetDelay)
                        sleep(tweetDelay)
                    else:
                        logger.error(f"Error tweeting frame {currentFrame}.")
                else:
                    logger.error(f"Frame {currentFrame} not found in {frame_dir}. Moving to next frame.")
                    config_data[f'currentFrame_{currentMovie}'] = str(int(currentFrame) + 1)
                    save_config(config_path, config_data)

        except Exception as e:
            print_error()
            break

if __name__ == "__main__":
    process_frames()
