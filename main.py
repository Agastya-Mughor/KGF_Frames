import os
import sys
import logging
import tweepy
import requests
import yaml
import signal
import time
from datetime import timedelta, datetime
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential

# Constants
FRAME_EXTENSION = '.jpg'
BATCH_PREFIX = 'batch_'
CONFIG_FILE = 'config.yaml'
LOG_FILE = 'log.txt'
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 2

# Store the working directory
DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables
load_dotenv()

# Access the environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_KEY_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
RESET_START = os.getenv("RESET_START", "False").lower() == "true"

# Configurable values
FRAME_DIRS = {
    int(key.split('_')[-1]): value
    for key, value in os.environ.items()
    if key.startswith("FRAMES_DIR_")
}
HASHTAGS = os.getenv("HASHTAGS", "#YashBoss\n#KGF_Frames")

class CombinedRotatingFileHandler(RotatingFileHandler, TimedRotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False, when='h', interval=1, utc=False):
        RotatingFileHandler.__init__(self, filename, mode, maxBytes, backupCount, encoding, delay)
        TimedRotatingFileHandler.__init__(self, filename, when, interval, backupCount, encoding, delay, utc)

    def shouldRollover(self, record):
        return RotatingFileHandler.shouldRollover(self, record) or TimedRotatingFileHandler.shouldRollover(self, record)

    def doRollover(self):
        RotatingFileHandler.doRollover(self)
        TimedRotatingFileHandler.doRollover(self)

# Set up logging
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    log_handler = CombinedRotatingFileHandler(
        f"{DIR}/{LOG_FILE}",
        maxBytes=MAX_LOG_SIZE,
        backupCount=LOG_BACKUP_COUNT,
        when="midnight",
        interval=1
    )
    log_handler.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)

    logger.addHandler(log_handler)

    logger.info("\n" + "="*80 + "\nNew Session Started\n" + "="*80 + "\n")
    logger.info("Every Frame In Order Twitter Bot started")

    return logger

logger = setup_logging()

def validate_env_vars():
    required_vars = [
        "API_KEY", "API_KEY_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET",
        "MAILGUN_API_KEY", "MAILGUN_DOMAIN", "RECIPIENT_EMAIL"
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        sys.exit(error_msg)

validate_env_vars()

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def send_email(subject: str, message: str) -> bool:
    if not EMAIL_ENABLED:
        return False

    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": f"Twitter Bot <mailgun@{MAILGUN_DOMAIN}>",
                "to": [RECIPIENT_EMAIL],
                "subject": subject,
                "text": message
            }
        )
        response.raise_for_status()
        logger.info(f"Email sent: {subject}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send email: {e}")
        raise

def authenticate_twitter() -> Tuple[tweepy.API, tweepy.Client]:
    try:
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api = tweepy.API(auth, wait_on_rate_limit=True, retry_count=3, retry_delay=120, retry_errors={503})
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)
        return api, client
    except Exception as e:
        logger.error("Error during Twitter authentication")
        logger.exception(e)
        send_email("Twitter Bot Error", f"Error during Twitter authentication: {str(e)}")
        sys.exit("Twitter authentication failed")

class ConfigManager:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config_data = self.load_config()
        self.last_saved = self.config_data.copy()

    def load_config(self) -> Dict:
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as config_file:
                return yaml.safe_load(config_file)
        else:
            return {
                'tweetDelay': 1800,
                'currentMovie': 1,
                **{f'currentFrame_{i}': 1 for i in FRAME_DIRS.keys()},
            }

    def save_config(self):
        if self.config_data != self.last_saved:
            try:
                with open(self.config_file, 'w') as config_file:
                    yaml.dump(self.config_data, config_file)
                self.last_saved = self.config_data.copy()
                logger.info("Configuration saved successfully.")
            except Exception as e:
                logger.error(f"Error saving configuration: {e}")

    def get(self, key: str, default=None):
        return self.config_data.get(key, default)

    def set(self, key: str, value):
        self.config_data[key] = value

config_manager = ConfigManager(f"{DIR}/{CONFIG_FILE}")

class FrameManager:
    def __init__(self):
        self.frame_cache = {}

    def cache_frames(self):
        for movie_number, frame_dir in FRAME_DIRS.items():
            frame_path = f"{DIR}/{frame_dir}"
            self.frame_cache[movie_number] = {}
            batch_folders = sorted([folder for folder in os.listdir(frame_path) if folder.startswith(BATCH_PREFIX)])
            for batch_folder in batch_folders:
                batch_path = os.path.join(frame_path, batch_folder)
                frames = [int(f.split('_')[1].split('.')[0]) for f in os.listdir(batch_path) if f.endswith(FRAME_EXTENSION)]
                for frame in frames:
                    self.frame_cache[movie_number][frame] = os.path.join(batch_path, f"frame_{frame}{FRAME_EXTENSION}")

    def get_total_frames(self, movie_number: int) -> int:
        return len(self.frame_cache.get(movie_number, {}))

    def find_frame(self, movie_number: int, frame_number: int) -> Optional[str]:
        return self.frame_cache.get(movie_number, {}).get(frame_number)

frame_manager = FrameManager()

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def tweet_frame(client: tweepy.Client, full_tweet: str, media: tweepy.Media) -> bool:
    try:
        client.create_tweet(text=full_tweet, media_ids=[media.media_id])
        logger.info("Tweet sent successfully.")
        return True
    except tweepy.TweepError as e:
        logger.error(f"Twitter API error in tweet_frame: {e}")
        if e.api_code == 187:
            logger.warning("Duplicate tweet detected. Skipping this frame.")
            return False
        elif e.api_code == 186:
            logger.error("Tweet exceeds character limit. Adjusting tweet content.")
            return False
        elif e.api_code == 144:
            logger.error("Tweet with media failed. Attempting without media.")
            try:
                client.create_tweet(text=full_tweet)
                logger.info("Tweet sent successfully without media.")
                return True
            except tweepy.TweepError as e2:
                logger.error(f"Failed to send tweet without media: {e2}")
                raise
        else:
            raise
    except Exception as e:
        logger.error(f"Unexpected error in tweet_frame: {e}")
        raise

def estimate_time_remaining(current_frame: int, total_frames: int, tweet_delay: int) -> str:
    remaining_frames = total_frames - current_frame
    seconds_remaining = remaining_frames * tweet_delay
    time_remaining = timedelta(seconds=seconds_remaining)
    return str(time_remaining)

def process_frames(api: tweepy.API, client: tweepy.Client):
    tweet_interval = timedelta(seconds=config_manager.get('tweetDelay', 1800))
    next_tweet_time = datetime.now().replace(second=0, microsecond=0)
    next_tweet_time += timedelta(minutes=30 - (next_tweet_time.minute % 30))

    while True:
        current_movie = config_manager.get('currentMovie', 1)
        frame_dir = FRAME_DIRS.get(current_movie)
        current_frame = config_manager.get(f'currentFrame_{current_movie}', 1)

        logger.info(f"Processing Movie {current_movie} - Current frame: {current_frame}")

        try:
            total_frames = frame_manager.get_total_frames(current_movie)
            logger.info(f"Total number of frames in the movie: {total_frames}")

            time_remaining = estimate_time_remaining(current_frame, total_frames, tweet_interval.total_seconds())
            logger.info(f"Estimated time remaining: {time_remaining}")

            if current_frame > total_frames:
                logger.info(f"All frames processed for Movie {current_movie}.")
                next_movie_number = current_movie + 1
                if next_movie_number in FRAME_DIRS:
                    config_manager.set('currentMovie', next_movie_number)
                    config_manager.set(f'currentFrame_{next_movie_number}', 1)
                    logger.info(f"Switching to Movie {next_movie_number}")
                else:
                    logger.info("No more movies to process. Stopping the bot.")
                    send_email("Twitter Bot Completed", "All movies have been processed.")
                    break
            else:
                frame_full_path = frame_manager.find_frame(current_movie, current_frame)

                if frame_full_path:
                    logger.info(f"Found frame file: {frame_full_path}")

                    sleep_time = (next_tweet_time - datetime.now()).total_seconds()
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                    media = api.media_upload(filename=frame_full_path)
                    frames_text = f"#KGF{current_movie} - Frame {current_frame} of {total_frames}"
                    full_tweet = f"{frames_text}\n\n{HASHTAGS}"

                    if tweet_frame(client, full_tweet, media):
                        logger.info(f"Successfully tweeted frame {current_frame}")
                        config_manager.set(f'currentFrame_{current_movie}', current_frame + 1)
                        config_manager.save_config()
                    else:
                        logger.error("Failed to send tweet.")
                        send_email("Twitter Bot Error", f"Failed to send tweet for Frame {current_frame}.")

                    next_tweet_time += tweet_interval
                else:
                    logger.error(f"Frame file not found: frame_{current_frame}{FRAME_EXTENSION}")
                    send_email("Twitter Bot Error", f"Frame file not found: frame_{current_frame}{FRAME_EXTENSION}")
                    config_manager.set(f'currentFrame_{current_movie}', current_frame + 1)
                    config_manager.save_config()

        except tweepy.TweepError as e:
            logger.error(f"Twitter API error: {e}")
            if e.api_code == 429:
                logger.info("Rate limit exceeded. Waiting for 15 minutes.")
                time.sleep(900)
            else:
                logger.exception(e)
                send_email("Twitter Bot Error", f"Twitter API error: {str(e)}")
                time.sleep(60)
        except Exception as e:
            logger.error("An unexpected error occurred.")
            logger.exception(e)
            send_email("Twitter Bot Error", f"An unexpected error occurred: {str(e)}")
            time.sleep(60)

        if datetime.now() > next_tweet_time:
            next_tweet_time = datetime.now().replace(second=0, microsecond=0)
            next_tweet_time += timedelta(minutes=30 - (next_tweet_time.minute % 30))

def signal_handler(signum, frame):
    logger.info("Received shutdown signal. Cleaning up...")
    config_manager.save_config()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    api, client = authenticate_twitter()

    if RESET_START:
        config_manager.set('currentMovie', 1)
        for movie_number in FRAME_DIRS.keys():
            config_manager.set(f'currentFrame_{movie_number}', 1)
        logger.info("RESET_START is True. Resetting state to start from movie 1.")
        config_manager.save_config()

    frame_manager.cache_frames()
    process_frames(api, client)

if __name__ == "__main__":
    main()