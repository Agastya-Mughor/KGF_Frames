import os
import sys
import logging
import traceback
import tweepy
import requests
from datetime import timedelta
from time import sleep

# Store the working directory
dir = os.path.abspath(os.path.dirname(__file__))

# Begin logging
logging.basicConfig(filename=f"{dir}/log.txt", level=logging.INFO)

print("Every Frame In Order Twitter Bot\n")
logging.info("Every Frame In Order Twitter Bot\n")

# Load configuration from secrets
config_data = {
    'tweetDelay': '30',  # Number of seconds between each tweet
    'currentFrame': '1',  # Current frame, will be updated by bot
}

# Twitter access tokens from Replit's Secrets tab
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_KEY_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Authenticating with Twitter
auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token,
                                access_secret)
api = tweepy.API(auth,
                 wait_on_rate_limit=True,
                 retry_count=3,
                 retry_delay=120,
                 retry_errors=set([503]))
client = tweepy.Client(consumer_key=api_key,
                       consumer_secret=api_secret,
                       access_token=access_token,
                       access_token_secret=access_secret)

# Number of seconds between tweets
tweetDelay = int(config_data['tweetDelay'])

# Path to frame directory
frame_dir = "frames"
frame_path = f"{dir}/{frame_dir}"


# Function to get time remaining in a readable format
def get_time_remaining(sec):
    timedelta_str = str(timedelta(seconds=sec))
    x = timedelta_str.split(':')
    dh = x[0]
    m = x[1]
    s = x[2]
    print(f"Time remaining: {dh} hours {m} minutes {s} seconds")
    logging.info(f"Time remaining: {dh} hours {m} minutes {s} seconds")


# Store traceback exception and print to console and log
def print_error():
    error = traceback.format_exc()
    print(error)
    logging.exception(
        "An exception was thrown and the bot might have stopped posting!")


for m in range(1):  # Only one movie
    while True:

        currentFrame = config_data['currentFrame']
        print("Current frame: ", currentFrame, "\n")
        logging.info(f"Current frame: {currentFrame}")

        try:
            # Counts number of frames in folder and store it in a variable
            totalFrames = len([
                f for f in os.listdir(frame_path)
                if os.path.isfile(os.path.join(frame_path, f))
            ])
            print('Total number of frames:', totalFrames)
            logging.info(f"Total number of frames: {totalFrames}")

            # Process a single frame
            image_path = f"{frame_path}/frame_{currentFrame}.jpg"
            print(f"Checking if file exists at: {image_path}")
            logging.info(f"Checking if file exists at: {image_path}")
            if os.path.isfile(image_path):
                # Uploading image of frame to Twitter
                print(f"Uploading image of frame {currentFrame} to Twitter")
                logging.info(
                    f"Uploading image of frame {currentFrame} to Twitter")
                media = api.media_upload(image_path)

                if media and hasattr(media, 'media_id'):
                    # Tweet text
                    framestext = f"Frame {currentFrame}"
                    full_tweet = f"{framestext} out of {totalFrames}"

                    # Send tweet with uploaded image and text
                    print(
                        f"Sending tweet with frame {currentFrame} out of {totalFrames}"
                    )
                    logging.info(
                        f"Sending tweet with frame {currentFrame} out of {totalFrames}"
                    )
                    client.create_tweet(text=full_tweet,
                                        media_ids=[media.media_id])

                    # Calculate remaining frames left
                    remainingFrames = totalFrames - int(currentFrame)
                    secondsleft = remainingFrames * tweetDelay
                    get_time_remaining(secondsleft)

                    # Save current frame progress to config
                    print("Saving progress to config")
                    logging.info("Saving progress to config")
                    currentFrame = int(currentFrame) + 1
                    config_data['currentFrame'] = str(currentFrame)

                    # Log progress update
                    logging.info(f"Updated current frame to {currentFrame}")

                    # Sleep for specified time before posting next frame
                    sleep(tweetDelay)
                else:
                    print(f"Failed to upload media for frame {currentFrame}")
                    logging.error(
                        f"Failed to upload media for frame {currentFrame}")
                    break  # Consider retrying instead of breaking
            else:
                print(f"Frame {currentFrame} does not exist")
                logging.error(f"Frame {currentFrame} does not exist")
                break  # Consider stopping or skipping instead of breaking

        except tweepy.TwitterServerError as tweepyServerError:
            if tweepyServerError.response.status_code == 503:
                logging.exception(
                    f'Twitter API: 503 Service Unavailable on frame {currentFrame}'
                )
                print(
                    f'Twitter API: 503 Service Unavailable on frame {currentFrame}'
                )
                # Sleep and retry logic for 503 errors
                sleep(tweetDelay)
                continue
        except requests.exceptions.ConnectionError:
            print_error()
            sleep(540)
            continue
        except Exception:
            print_error()
            sleep(tweetDelay)
            continue
        else:
            logging.info("No exceptions, continuing to the next frame.")
            continue  # Ensure the loop continues

# Store traceback exception and print to console and log
error = traceback.format_exc()
print(error)
logging.exception(
    "If you are reading this then the bot has likely finished, if so congrats! if not an error occurred."
)
print(
    "If you are reading this then the bot has likely finished, if so congrats! if not an error occurred."
)
