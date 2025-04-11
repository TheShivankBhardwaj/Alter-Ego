import google.generativeai as genai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import json
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
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
        query = f"{self.name} {self.occupation} interview | podcast | ted talk -inurl:(live stream)" if self.occupation else f"{self.name} interview | podcast | ted talk -inurl:(live stream)"
        request = self.youtube.search().list(
            q=query,
            part="id,snippet",
            type="video",
            maxResults=10,
            videoCaption="closedCaption",
            order="date"
        )
        response = request.execute()
        video_ids = [item["id"]["videoId"] for item in response["items"]]
        print(f"Fetched latest videos for {self.name}: {video_ids}")
        return video_ids

    def _get_transcripts(self):
        if os.path.exists(self.transcript_file):
            with open(self.transcript_file, "r") as f:
                transcripts = json.load(f)
            print(f"Loaded cached transcripts for {self.name} from {self.transcript_file}")
            return transcripts

        video_ids = self._fetch_videos()
        transcripts = []
        for video_id in video_ids:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                text = " ".join([entry["text"] for entry in transcript])
                transcripts.append({"text": text})
                print(f"Grabbed transcript for {video_id}")
                if len(transcripts) >= 5:
                    break
            except Exception as e:
                print(f"Skipped {video_id}: {e}")

        if not transcripts:
            raise Exception("No transcripts found—try a different persona.")
        with open(self.transcript_file, "w") as f:
            json.dump(transcripts, f)
        print(f"Saved {len(transcripts)} transcripts for {self.name} to {self.transcript_file}")
        return transcripts

    def _build_persona(self):
        transcripts = self._get_transcripts()
        prompt = f"I am {self.name}, a{'n' if self.occupation and self.occupation[0] in 'aeiou' else ''} {self.occupation if self.occupation else 'person'}. My voice is forged from these recent spoken words: "
        for entry in transcripts:
            prompt += f"'{entry['text'][:300]}...', "
        prompt += (
            f"I embody {self.name}’s unique style—mimicking their exact phrasing, slang, and quirks from these latest transcripts. "
            f"Capture their personality vividly as a {self.occupation if self.occupation else 'person'}: their passion, humor, intensity, or charm. "
            f"Respond as they would, staying true to their current world—sharp, authentic, and in character—no fluff or generic filler."
        )
        return prompt

    def chat(self, user_input):
        full_prompt = f"{self.persona_prompt}\nUser says: '{user_input}'"
        response = self.model.generate_content(full_prompt)
        return response.text.strip()