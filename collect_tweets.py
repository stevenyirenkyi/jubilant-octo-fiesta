from dotenv import load_dotenv
from os import environ
from tweepy import Client, Paginator, Tweet, Response
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Any
from db import get_collection
from datetime import datetime

import requests


load_dotenv()


def run(client: Client, limit=None, max_result=100):
    query = "(unvaccinated OR vaccine) (#unvaccinated OR #vaccine OR #vaccineinjuries OR #VaccineSideEffects OR #vaccinedamage OR #VaccineInjured OR #StoptheShots) lang:en -is:retweet -is:reply -is:quote -has:media -has:images"
    date_pattern = "%Y-%m-%d"
    start_time = datetime.strptime("2022-07-06", date_pattern)
    end_time = datetime.strptime("2022-08-06", date_pattern)

    for response in Paginator(client.search_all_tweets, query, start_time=start_time, end_time=end_time, max_results=max_result,
                              tweet_fields=["author_id", "public_metrics", "entities"], limit=limit):
        response: Response
        if response.data is None:
            continue

        for tweet in response.data:
            tweet: Tweet

            tweet_features = extract_tweet_features(tweet)
            tweet_features["created_at"] = datetime.today()
            collection.insert_one(tweet_features)


def get_webpage_meta(url: str, tweet_id: str) -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        og_title = soup.find("meta", property="og:title")
        og_description = soup.find("meta", property="og:description")
        title = soup.title
        description = soup.find("meta", attrs={"name": "description"})

        return {
            "title": og_title["content"] if og_title else title.string if title else "",
            "description": og_description["content"] if og_description else description["content"] if description else ""
        }

    except requests.exceptions.ConnectionError:
        # TODO: LOG ERRORS
        return None
    except Exception as e:
        print(e)
        return None


def get_hashtags(tweet: Tweet) -> dict:
    entities = tweet.entities
    if entities is None:
        return dict(hashtag_count=0, hashtags="")

    hashtag_list = entities.get("hashtags")
    if hashtag_list is None:
        return dict(hashtag_count=0, hashtags="")

    hashtags = []
    for hashtag_dict in hashtag_list:
        hashtags.append(hashtag_dict["tag"])

    return dict(hashtag_count=len(hashtags), hashtags=" ".join(hashtags))


def get_urls(tweet: Tweet) -> dict[str, Any]:
    error_dict = dict(webpage_description="",
                      webpage_title="", url_count=0, url="")
    entities = tweet.entities
    if entities is None:
        return error_dict

    url_list = entities.get("urls")
    if url_list is None:
        return error_dict

    descriptions = []
    titles = []
    urls = []
    for url_dict in url_list:
        url = url_dict.get("unwound_url") or url_dict.get("expanded_url")

        if url.startswith("https://twitter.com/"):
            descriptions.append("twitter_link")
            titles.append("twitter_link")
            urls.append(url)
            continue

        meta = get_webpage_meta(url, tweet.id)
        if meta is None:
            continue
        descriptions.append(meta.get("description"))
        titles.append(meta.get("title"))
        urls.append(url)

    delimiter = " ♣♣ "
    return{
        "webpage_description": delimiter.join(descriptions),
        "webpage_title": delimiter.join(titles),
        "url_count": len(urls),
        "url": delimiter.join(urls)
    }


def extract_tweet_features(tweet: Tweet):
    result = dict(tweet_id=tweet.id, tweet_text=tweet.text,
                  author_id=tweet.author_id)
    result.update(tweet.public_metrics)
    result.update(get_hashtags(tweet))
    result.update(get_urls(tweet))

    return result


if __name__ == "__main__":
    client = Client(
        bearer_token=environ["ACADEMIC_BEARER_TOKEN"], wait_on_rate_limit=True)
    collection = get_collection("all_tweets")

    tweets = run(client, limit=1, max_result=10)
