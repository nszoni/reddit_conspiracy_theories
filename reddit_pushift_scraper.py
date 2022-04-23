import praw
from psaw import PushshiftAPI
import datetime as dt
import pandas as pd
from tqdm import tqdm
import os

def get_date(created) -> str:
    return dt.fromtimestamp(created)

def pushshift_connection(subreddit, limit, ubound, lbound):

    start_epoch=int(dt.datetime(lbound, 1, 1).timestamp())
    end_epoch=int(dt.datetime(ubound, 12, 31).timestamp())

    # Initialize PushShift
    api = PushshiftAPI()

    #retrieve id from pushift
    gen = api.search_submissions(
        after=start_epoch,
        before=end_epoch,
        filter=['id'],
        subreddit=subreddit,
        limit=limit
    )

    return gen

def praw_connection():

    # to use PRAW
    reddit = praw.Reddit(
        client_id = os.environ["REDDIT_CLIENT_ID"], \
        client_secret = os.environ["REDDIT_CLIENT_SECRET"], \
        user_agent = os.environ["REDDIT_APP_NAME"], \
        username = os.environ["REDDIT_USER_NAME"], \
        password = os.environ["REDDIT_LOGIN_PASSWORD"],
    )

    return reddit

def get_data(gen, reddit) -> pd.DataFrame:

    #init empty dictionary
    submissions_dict = {
        "id" : [],
        "author" : [],
        "url" : [],
        "title" : [],
        "score" : [],
        "num_comments": [],
        "created" : [],
        "body" : [],
    }

    #use praw to search by id
    for submission_psaw in tqdm(gen):
        # use psaw here
        submission_id = submission_psaw.d_['id']
        # use praw from now on
        submission_praw = reddit.submission(id=submission_id)

        submissions_dict["id"].append(submission_praw.id)
        submissions_dict["author"].append(submission_praw.author)
        submissions_dict["url"].append(submission_praw.url)
        submissions_dict["title"].append(submission_praw.title)
        submissions_dict["score"].append(submission_praw.score)
        submissions_dict["num_comments"].append(submission_praw.num_comments)
        submissions_dict["created"].append(submission_praw.created_utc)
        submissions_dict["body"].append(submission_praw.selftext)

    submissions_df = pd.DataFrame(submissions_dict)

    return submissions_df

def save_data(submissions_df, ubound = '', lbound = ''):
    submissions_df.to_csv(f'./data/reddit_ct_pushift_{lbound}_{ubound}.csv', header=True, index=False)


if __name__ == "__main__":
    subreddit="conspiracy"
    limit=2500
    ubound=2019
    lbound=2018
    gen = pushshift_connection(subreddit, limit, ubound, lbound)
    reddit = praw_connection()
    submissions = get_data(gen, reddit)
    save_data(submissions, ubound, lbound)
