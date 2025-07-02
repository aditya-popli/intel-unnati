# Installation (if not already done):
# pip install gradio requests beautifulsoup4 lxml

import gradio as gr
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time
from typing import List, Tuple, Dict
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_bing_images(self, topic: str, limit: int = 5) -> List[str]:
        """Scrape high-quality image URLs from Bing"""
        try:
            search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(topic)}&form=HDRSC2"
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Bing request failed: {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            images = []
            for tag in soup.find_all("a", class_="iusc"):
                m_json = tag.get("m")
                if m_json:
                    match = re.search(r'"murl":"(.*?)"', m_json)
                    if match:
                        url = match.group(1).replace('\\u002f', '/').replace('\\', '')
                        if url.startswith("http") and not url.endswith(".webp"):
                            images.append(url)
                if len(images) >= limit:
                    break
            return images
        except Exception as e:
            logger.error(f"Error scraping Bing: {e}")
            return []

    def scrape_youtube_videos(self, topic: str, limit: int = 3) -> List[Dict[str, str]]:
        """Scrape YouTube video links."""
        try:
            query = f"{topic} educational"
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"YouTube request failed: {response.status_code}")
                return []

            pattern = r'"videoId":"(.*?)".*?"title":{"runs":\[{"text":"(.*?)"}\]'
            matches = re.findall(pattern, response.text)
            videos = []
            seen = set()
            for vid, title in matches:
                if vid not in seen:
                    videos.append({"title": title, "url": f"https://www.youtube.com/watch?v={vid}"})
                    seen.add(vid)
                if len(videos) >= limit:
                    break
            return videos
        except Exception as e:
            logger.error(f"Error scraping YouTube: {e}")
            return []

    def search(self, topic: str) -> Tuple[List[str], List[Dict[str, str]]]:
        if not topic.strip():
            return [], []
        logger.info(f"Searching content for topic: {topic}")
        images = self.scrape_bing_images(topic)
        videos = self.scrape_youtube_videos(topic)
        time.sleep(0.5)
        return images, videos

scraper = ContentScraper()

def search_content(topic: str) -> Tuple[List[str], str]:
    if not topic.strip():
        return [], "Please enter a valid topic."
    try:
        images, videos = scraper.search(topic)
        video_md = "\n".join([f"{i+1}. [{v['title']}]({v['url']})" for i, v in enumerate(videos)])
        return images, video_md if video_md else "No videos found."
    except Exception as e:
        logger.error(f"Search error: {e}")
        return [], f"Error: {e}"

def create_interface():
    with gr.Blocks(title="Educational Content Finder", theme=gr.themes.Soft()) as interface:
        gr.Markdown("""
        # 🎓 Educational Content Finder
        Search for high-quality images and YouTube videos on any topic.
        """)
        with gr.Row():
            topic_input = gr.Textbox(label="Topic", placeholder="e.g., Photosynthesis")
            search_btn = gr.Button("🔍 Search")
        with gr.Row():
            image_gallery = gr.Gallery(label="📸 Images", columns=3, rows=2)
            video_markdown = gr.Markdown("Enter a topic and click Search to begin.")

        search_btn.click(fn=search_content, inputs=[topic_input], outputs=[image_gallery, video_markdown])
        topic_input.submit(fn=search_content, inputs=[topic_input], outputs=[image_gallery, video_markdown])
    return interface

if __name__ == "__main__":
    print("🚀 Starting Educational Content Finder at http://127.0.0.1:7860")
    create_interface().launch(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True)
