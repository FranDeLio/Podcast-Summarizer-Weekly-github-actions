import requests
import traceback
import re
import dateutil.parser
from datetime import datetime
import tiktoken
from bs4 import BeautifulSoup, Tag
import assemblyai as aai
from openai import OpenAI
from dotenv import load_dotenv; load_dotenv()

from os import listdir, makedirs
from os.path import isfile, join

from config import PODCASTS_DICT, START_DATE, GPT_MODEL, TEMPERATURE, MAX_TOKEN_LENGTH, MAX_STRING_LENGTH


def list_all_downloaded_episodes(mypath: str) -> list[str]:
    onlyfiles = [
        f.replace(".md", "") for f in listdir(mypath) if isfile(join(mypath, f))
    ]

    return onlyfiles


def get_episode_date(episode: Tag) -> datetime.date:
    date_text = episode.find("pubDate").text
    parsed_date = dateutil.parser.parse(date_text).strftime("%d-%m-%Y")
    parsed_date = datetime.strptime(parsed_date, "%d-%m-%Y").date()

    return parsed_date


def get_simplified_episode_title(episode: Tag) -> str:
    title = episode.find("title").text
    simplified_title = re.sub(r"[%/&!@#–\*\$\?\+\^\\.\\\\]", "", title).replace(
        "Episode", ""
    )

    return simplified_title


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def download_transcribed_episode(episode: Tag) -> str:
    mp3_url = episode.find("enclosure")["url"]
    aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]
    transcriber = aai.Transcriber()

    config = aai.TranscriptionConfig()  # audio_end_at=5000
    transcription_result = transcriber.transcribe(mp3_url, config=config)

    if transcription_result.status == "completed":
        return transcription_result.text
    return "transcription_error"


def summarize_transcription(transcription: str) -> None:
    client = OpenAI()

    system_txt = "You are an assistant, who identifies the key points within podcast transcripts and explains them in detail."
    completion = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": system_txt},
            {
                "role": "user",
                "content": f"Summarize the following text: {transcription}",
            },
        ],
        temperature=TEMPERATURE,
    )

    output = completion.choices[0].message.content

    return output


def main() -> None:
    for podcast, rss_feed_url in PODCASTS_DICT.items():
        summaries_path = f"./podcast_episode_summaries/{podcast}"
        makedirs(summaries_path, exist_ok=True)
        downloaded_episodes = list_all_downloaded_episodes(summaries_path)

        page = requests.get(rss_feed_url)
        soup = BeautifulSoup(page.content, "xml")
        podcast_episodes = soup.find_all("item")

        for episode in podcast_episodes:
            title = get_simplified_episode_title(episode)
            if (
                get_episode_date(episode) > START_DATE
                and title not in downloaded_episodes
            ):
                print(title)
                summary_path = f"{summaries_path}/{title}.md"
                transcription = download_transcribed_episode(episode)
                
                if transcription == "transcription_error":
                    continue

                if num_tokens_from_string(transcription) > MAX_TOKEN_LENGTH:
                    transcription = transcription[0:MAX_STRING_LENGTH]

                try:
                    summary = summarize_transcription(transcription)
                except Exception:
                    summary = traceback.format_exc()
                    print(summary)

                with open(summary_path, "w+") as f:
                    f.write(summary)


if __name__ == "__main__":
    main()

   
