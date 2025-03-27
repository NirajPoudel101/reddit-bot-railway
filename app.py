import praw
import time
import threading
from flask import Flask, jsonify
from datetime import datetime

# Reddit API credentials (read-only)
reddit = praw.Reddit(
    client_id="o1jq6g9NaxvKnym_oQvO3Q",
    client_secret="VnsMkYQBKzzcMaGjuA015Ge4fQ0XzA",
    user_agent="python:FlairNotifierBot:v1.0 (by u/wasteOfSoch)",
)
print("Connected to Reddit as:", reddit.user.me())

# Flask app setup
app = Flask(__name__)

# Targets
targets = {
    "youtubeeditorsforhire": [],
    "creatorservices": ["looking for paid services"],
    "findvideoeditors": [],
    "askreddit": []
}

subreddit_list = "+".join(targets.keys())
print("Monitoring subreddits:", subreddit_list)

# Store collected posts
collected_posts = []

# Bot function
def run_reddit_bot():
    seen_posts = set()
    while True:
        try:
            subreddit = reddit.subreddit(subreddit_list)
            print("Streaming started...")
            for submission in subreddit.stream.submissions(skip_existing=True):
                if submission.id not in seen_posts:
                    subreddit_name = submission.subreddit.display_name.lower()
                    flair = submission.link_flair_text if submission.link_flair_text else "None"
                    if subreddit_name in targets:
                        target_flairs = [f.lower() for f in targets[subreddit_name]]
                        if not target_flairs or (flair.lower() in target_flairs):
                            post_data = {
                                "title": submission.title[:256],
                                "url": f"https://reddit.com{submission.permalink}",
                                "subreddit": subreddit_name,
                                "flair": flair,
                                "author": submission.author.name,
                                "timestamp": datetime.utcfromtimestamp(submission.created_utc).isoformat() + "Z",
                                "description": submission.selftext[:500] if submission.selftext else "No preview",
                                "thumbnail": submission.thumbnail if submission.thumbnail.startswith("http") else None
                            }
                            collected_posts.append(post_data)
                            if len(collected_posts) > 100:
                                collected_posts.pop(0)
                    seen_posts.add(submission.id)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)
        time.sleep(5)

# API endpoint
@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(collected_posts)

# Start bot in background
bot_thread = threading.Thread(target=run_reddit_bot, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)