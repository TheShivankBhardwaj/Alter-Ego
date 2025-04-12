import google.generativeai as genai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import json
import os
#import streamlit as st
from dotenv import load_dotenv
import os

# Load from .env file
load_dotenv()

# Now you can access them like this:
GEMINI_API_KEY= os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# Improved conditional key loading
# GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
# YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)

class PersonaBot:
    def __init__(self, name, occupation=""):
        self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.name = name
        self.occupation = occupation
        self.transcript_dir = "transcripts"
        if not os.path.exists(self.transcript_dir):
            os.makedirs(self.transcript_dir)
        self.transcript_file = os.path.join(self.transcript_dir, f"{self.name.lower().replace(' ', '_')}_transcripts.json")
        self.persona_prompt = self._build_persona()

    def _fetch_videos(self):
        base_query = f"{self.name} {'chai aur code' if 'chai' in self.occupation.lower() else self.occupation} interview podcast ted talk discussion speech -inurl:(live stream) full hindi english subtitles"
        queries = [base_query]
        
        video_ids = []
        for query in queries:
            request = self.youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=20,
                order="relevance",
                regionCode="IN"
            )
            response = request.execute()
            new_ids = [item["id"]["videoId"] for item in response["items"] if item["id"]["videoId"] not in video_ids]
            video_ids.extend(new_ids)
            if len(video_ids) >= 10:
                break
            print(f"Tried query: {query}, found {len(new_ids)} new videos")

        print(f"Fetched videos for {self.name}: {video_ids}")
        return video_ids[:10]

    def _get_transcripts(self):
        if os.path.exists(self.transcript_file):
            with open(self.transcript_file, "r") as f:
                transcripts = json.load(f)
            print(f"Loaded cached transcripts for {self.name} from {self.transcript_file}")
            return transcripts

        video_ids = self._fetch_videos()
        transcripts = []
        attempted_video_ids = []

        for video_id in video_ids:
            attempted_video_ids.append(video_id)
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi', 'en', 'auto'])
                text = " ".join([entry["text"] for entry in transcript])
                transcripts.append({"text": text, "video_id": video_id})
                print(f"Grabbed transcript for video ID: {video_id} (language: {transcript[0]['language']} if available)")
            except Exception as e:
                print(f"Transcript failed for {video_id}: {e}")
                continue

            if len(transcripts) >= 5:
                break

        if not transcripts:
            # st.error(f"No transcripts found for {self.name}. Attempted video IDs: {attempted_video_ids}. Check API keys or connectivity.")
            raise Exception("No transcripts found—try a different persona or check API keys/connectivity.")
        with open(self.transcript_file, "w") as f:
            json.dump(transcripts, f)
        print(f"Attempted video IDs: {attempted_video_ids}")
        print(f"Saved {len(transcripts)} transcripts for {self.name} to {self.transcript_file} from video IDs: {[t['video_id'] for t in transcripts]}")
        return transcripts

    def _build_persona(self):
        transcripts = self._get_transcripts()
        prompt = (
            f"You are {self.name}, a{'n' if self.occupation and self.occupation[0] in 'aeiou' else ''} {self.occupation if self.occupation else 'person'} speaking as if in a casual, real-time conversation. "
            f"Your voice, tone, and personality are shaped entirely by these recent transcripts from your interviews, podcasts, and videos: "
        )
        for i, entry in enumerate(transcripts, 1):
            snippet = entry['text'][:500].rsplit(' ', 1)[0] + "..."
            prompt += f"\nTranscript {i}: '{snippet}'"
        prompt += (
            f"\n\nBased on these transcripts, adopt {self.name}'s exact way of speaking—copy their sentence structure, word choice, slang, pacing, and any verbal tics or quirks. "
            f"Reflect their personality traits—like how they express enthusiasm, humor, seriousness, or curiosity—and their typical attitude or worldview as shown in the transcripts. "
            f"If they ramble, you ramble. If they’re blunt, you’re blunt. If they geek out, you geek out. "
            f"Respond to the user as {self.name} would in a natural, unscripted chat, staying true to their current life and interests from the transcripts. "
            f"Keep it concise unless their style is long-winded, and avoid generic or robotic answers—make every word sound like it’s coming straight from {self.name}."
        )
        return prompt

    def chat(self, user_input):
        full_prompt = f"{self.persona_prompt}\nUser says: '{user_input}'"
        response = self.model.generate_content(full_prompt)
        return response.text.strip()
