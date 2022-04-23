import os
import praw
import pandas as pd
from datetime import datetime as dt
from tqdm import tqdm


def get_date(created) -> str:
    return dt.fromtimestamp(created)


def reddit_connection():
    client_id = os.environ["REDDIT_CLIENT_ID"]
    client_secret = os.environ["REDDIT_CLIENT_SECRET"]
    user_agent = os.environ["REDDIT_APP_NAME"]
    username = os.environ["REDDIT_USER_NAME"]
    password = os.environ["REDDIT_LOGIN_PASSWORD"]

    reddit = praw.Reddit(client_id=client_id, \
                         client_secret=client_secret, \
                         user_agent=user_agent, \
                         username=username, \
                         password=password)
    return reddit


def build_dataset(reddit, search_words='conspiracy', items_limit=3000, ubound=2000, lbound=2099, time_filter='all') -> pd.DataFrame:
    
    
    subreddit = reddit.subreddit(search_words)

    # Collect top, hot, rising, new reddit posts and merge it together to generate data
    top_subreddit = subreddit.top(time_filter, limit=items_limit)
    hot_subreddit = subreddit.hot(limit=items_limit)
    rising_subreddit = subreddit.rising(limit=items_limit)
    new_subreddit = subreddit.new(limit=items_limit)

    topics_dict = { "title":[],
                "score":[],
                "id":[], "url":[],
                "comms_num": [],
                "created": [],
                "body":[]}
    
    #controversies before the pandemix (before first case in Wuhan)
    print(f"retrieve reddit posts ...")
    for sub in (top_subreddit, hot_subreddit, rising_subreddit, new_subreddit):
        for submission in tqdm(sub):
            if dt.fromtimestamp(submission.created_utc).year <= ubound and dt.fromtimestamp(submission.created_utc).year >= lbound:
                topics_dict["title"].append(submission.title)
                topics_dict["score"].append(submission.score)
                topics_dict["id"].append(submission.id)
                topics_dict["url"].append(submission.url)
                topics_dict["comms_num"].append(submission.num_comments)
                topics_dict["created"].append(submission.created)
                topics_dict["body"].append(submission.selftext)

    print(f"retrieve reddit comments ...")
    for comment in tqdm(subreddit.comments(limit=2000)):
        if dt.fromtimestamp(comment.created_utc).year <= ubound and dt.fromtimestamp(comment.created_utc).year >= lbound:
            topics_dict["title"].append("Comment")
            topics_dict["score"].append(comment.score)
            topics_dict["id"].append(comment.id)
            topics_dict["url"].append("")
            topics_dict["comms_num"].append(0)
            topics_dict["created"].append(comment.created)
            topics_dict["body"].append(comment.body)

    topics_df = pd.DataFrame(topics_dict)
    print(f"top reddit posts retrieved: {len(topics_df)}")
    topics_df['timestamp'] = topics_df['created'].apply(lambda x: get_date(x))

    return topics_df
   

def update_and_save_dataset(topics_df, ubound='', lbound=''):   
    file_path = f"data/reddit_ct_{lbound}_{ubound}.csv"
    topics_df.to_csv(file_path, index=False)
    print(f"dataset saved to {file_path}")
    if os.path.exists(file_path):
        topics_old_df = pd.read_csv(file_path)
        print(f"past reddit posts: {topics_old_df.shape}")
        topics_all_df = pd.concat([topics_old_df, topics_df], axis=0)
        print(f"top reddit posts: {topics_df.shape[0]} past posts: {topics_old_df.shape[0]} all posts: {topics_all_df.shape[0]}")
        topics_top_df = topics_all_df.drop_duplicates(subset = ["id"], keep='last', inplace=False)
        print(f"all reddit posts: {topics_top_df.shape}")
        topics_top_df.to_csv(file_path, index=False)
    else:
        print(f"reddit posts: {topics_df.shape}")
        topics_df.to_csv(file_path, index=False)


if __name__ == "__main__":
    lbound = 2021
    ubound = 2022
    time_filter = 'all'
    reddit = reddit_connection()
    topics_data_df = build_dataset(reddit, ubound=ubound, lbound=lbound, time_filter=time_filter)
    update_and_save_dataset(topics_data_df, ubound, lbound)