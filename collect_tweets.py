from dotenv import load_dotenv
from os import environ
from tweepy import Client, Paginator, Tweet, Response
from datetime import datetime
from bs4 import BeautifulSoup
import requests

load_dotenv()


def search_tweets(client: Client) -> list[Tweet]:
    query = "(unvaccinated OR vaccine) (#unvaccinated OR #vaccine) lang:en -is:retweet -is:reply -is:quote -has:media -has:images"
    date_pattern = "%Y-%m-%d"
    start_time = datetime.strptime("2022-07-06", date_pattern)
    end_time = datetime.strptime("2022-08-06", date_pattern)
    tweets: list[Tweet] = []

    for response in Paginator(client.search_all_tweets, query, start_time=start_time, end_time=end_time, max_results=100,
                              tweet_fields=["author_id", "public_metrics", "entities"], limit=3):
        response: Response

        tweets.extend(response.data)

    return tweets


def get_webpage_meta(url: str) -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        return {
            "title": soup.title.string,
            "description": soup.find("meta", attrs={"name": "description"})["content"]
        }
    except:
        return None




if __name__ == "__main__":
    client = Client(
        bearer_token=environ["ACADEMIC_BEARER_TOKEN"], wait_on_rate_limit=True)

    # tweets = search_tweets(client)

    # for tweet in tweets:
    #     print(tweet.id)
    #     print(tweet.text)
    #     print("\n..........................................")

    url = "https://realpython.com/python-web-scraping-practical-introduction/"
    df = get_webpage_description(url)
    print(df)
