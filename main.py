import requests
from bs4 import BeautifulSoup
import time
import dateutil.parser
import os
import assemblyai as aai
from datetime import datetime
import re
from os import listdir
from os.path import isfile, join
#from dotenv import load_dotenv ; load_dotenv()

def get_episode_date(episode):

    date_text=episode.find('pubDate').text
    parsed_date=dateutil.parser.parse(date_text).strftime('%d-%m-%Y')
    parsed_date=datetime.strptime(parsed_date, '%d-%m-%Y').date()

    return parsed_date

def get_simplified_episode_title(episode):

    title = episode.find('title').text
    simplified_title = re.sub(r'[%/&!@#–\*\$\?\+\^\\.\\\\]', '', title).replace("Episode","")

    return simplified_title

def download_transcribed_episode(episode, transcripts_path):

    title = get_simplified_episode_title(episode)
    transcript_path = f"{transcripts_path}/{title}.txt"
    mp3_url = episode.find('enclosure')['url']

    aai.settings.api_key=os.environ['ASSEMBLYAI_API_KEY']
    transcriber = aai.Transcriber()

    config = aai.TranscriptionConfig() #audio_end_at=5000
    transcription_result = transcriber.transcribe(mp3_url, config=config)

    if transcription_result.status == 'completed':
        with open(transcript_path,'w+') as f:
            f.write(transcription_result.text)
    elif transcription_result.status == 'error':
        raise RuntimeError(f"Transcription failed: {transcription_result['error']}")
    else:
        time.sleep(3)

def list_all_downloaded_episodes(mypath):

    onlyfiles = [f.replace(".txt", "") for f in listdir(mypath) if isfile(join(mypath, f))]

    return onlyfiles


if __name__ == '__main__':

    podcasts_list = {'PhilosophizeThis': 'https://philosophizethis.libsyn.com/rss',
                    'LexFridman': 'https://lexfridman.com/feed/podcast/',
                    'EconTalk': 'https://feeds.simplecast.com/wgl4xEgL'}

    start_date = datetime.strptime('01-10-2023', '%d-%m-%Y').date()

    for podcast, rss_feed_url in podcasts_list.items():
        page = requests.get(rss_feed_url)
        soup = BeautifulSoup(page.content, 'xml')

        transcripts_path = f'./transcripts/{podcast}'
        os.makedirs(transcripts_path, exist_ok=True)
        downloaded_episodes = list_all_downloaded_episodes(transcripts_path)
        podcast_episodes = soup.find_all('item')

        for episode in podcast_episodes:
            if get_episode_date(episode)>start_date and get_simplified_episode_title(episode) not in downloaded_episodes:
                
                print(get_simplified_episode_title(episode))
                download_transcribed_episode(episode, transcripts_path)

            



