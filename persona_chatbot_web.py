import google.generativeai as genai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
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
        # Build search query with multiple keyword additions.
        base_query = f"{self.name} {self.occupation} interview OR podcast-inurl:(live stream)"
        additional_terms = ["full", "english", "Hindi"]
        queries = []
        for i in range(len(additional_terms) + 1):
            terms = " ".join(additional_terms[:i])
            queries.append(f"{base_query} {terms}".strip())

        video_ids = []
        for query in queries:
            request = self.youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=15,
                videoDuration="any",
                order="relevance",
                regionCode="IN"
            )
            response = request.execute()
            new_ids = [item["id"]["videoId"] for item in response["items"] if item["id"]["videoId"] not in video_ids]
            video_ids.extend(new_ids)
            print(f"Tried query: '{query}', found {len(new_ids)} new videos")
            if len(video_ids) >= 10:
                break

        print(f"Fetched videos for {self.name}: {video_ids}")
        return video_ids[:10]

    def _get_transcripts(self):
        # Use cached transcripts if available
        if os.path.exists(self.transcript_file):
            with open(self.transcript_file, "r") as f:
                transcripts = json.load(f)
            print(f"Loaded cached transcripts for {self.name} from {self.transcript_file}")
            return transcripts

        video_ids = self._fetch_videos()
        transcripts = []
        for video_id in video_ids:
            transcript_text = None
            # Attempt to get the official (manually created) transcript regardless of language.
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = " ".join([entry["text"] for entry in transcript])
                print(f"Grabbed official transcript for {video_id} (language preserved)")
            except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript) as e:
                print(f"Official transcript not found for {video_id}: {e}")
                # Fallback: try auto-generated captions in English or Hindi.
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "hi"])
                    transcript_text = " ".join([entry["text"] for entry in transcript])
                    print(f"Grabbed auto-generated transcript for {video_id} in English/Hindi")
                except Exception as inner_e:
                    print(f"Skipped {video_id}: {inner_e}")
            except Exception as exc:
                print(f"Error fetching transcript for {video_id}: {exc}")

            if transcript_text:
                transcripts.append({"text": transcript_text})
            if len(transcripts) >= 5:
                break

        if not transcripts:
            raise Exception("No transcripts found—try a different persona or check API keys/connectivity.")
        
        # Save transcripts to avoid refetching on subsequent runs.
        with open(self.transcript_file, "w") as f:
            json.dump(transcripts, f)
        print(f"Saved {len(transcripts)} transcripts for {self.name} to {self.transcript_file}")
        return transcripts

    def _build_persona(self):
        transcripts = self._get_transcripts()
        prompt = (
            f"You are {self.name}, a {self.occupation if self.occupation else 'person'} speaking in real time conversation "
            f"Your voice and tone should be entirely and your personality similar to theese transcripts from your interviews, podcasts, and videos: "
        )
        for i, entry in enumerate(transcripts, 1):
            
            snippet = entry['text'][:500].rsplit(' ', 1)[0] + "..."
            prompt += f"\nTranscript {i}: '{snippet}'"
        prompt += (
            f"\n\nBut only adopt {self.name}'s way of speaking and tone , texture ,way of spekaing and their slangs. "
            f"Try to guess in which language the user(the one asking question) is comfortable in and then answer in English or Either in Hinglish  "
            f"Don't show the translation or ask user to tell the comfortable language just blend the conversation accordingly"
            f"Speak as much as it is required do not be too rude nor too open , be genuine "
        )
        return prompt

    def chat(self, user_input):
        full_prompt = f"{self.persona_prompt}\nUser says: '{user_input}'"
        response = self.model.generate_content(full_prompt)
        return response.text.strip()


