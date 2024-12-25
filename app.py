import streamlit as st
import google.generativeai as genai
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import yt_dlp
from pathlib import Path
import pandas as pd
from typing import List, Dict
import json
from datetime import datetime
import os
from PIL import Image
import cv2
from moviepy.editor import VideoFileClip

class AdLibraryScraper:
    def __init__(self):
        # Set up Chrome options for headless operation
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Runs in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)

    def get_ad_library_url(self, page_name: str) -> str:
        """Convert Facebook page name to Ad Library URL"""
        # Format: https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=US&view_all_page_id=PAGE_ID
        base_url = "https://www.facebook.com/ads/library/"
        return f"{base_url}?active_status=all&ad_type=all&country=US&q={page_name}"

    def extract_video_urls(self, page_name: str) -> List[Dict]:
        """Scrape video ad URLs from Facebook Ad Library"""
        url = self.get_ad_library_url(page_name)
        self.driver.get(url)

        # Wait for ads to load
        time.sleep(5)  # Adjust based on page load time

        # Scroll to load more ads
        for _ in range(3):  # Adjust number of scrolls as needed
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # Find video ads
        video_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'] video")

        video_info = []
        for video in video_elements:
            try:
                # Get video source URL
                video_url = video.get_attribute("src")

                # Get ad text if available
                ad_container = video.find_element(By.XPATH, "./ancestor::div[contains(@class, '_7jyr')]")
                ad_text = ad_container.find_element(By.CSS_SELECTOR, "div._7jyw").text

                if video_url:
                    video_info.append({
                        "url": video_url,
                        "text": ad_text,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                st.warning(f"Error extracting video info: {str(e)}")

        return video_info

    def close(self):
        """Close the browser"""
        self.driver.quit()

def download_video(url: str, output_path: str) -> str:
    """Download video using yt-dlp"""
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        st.error(f"Error downloading video: {str(e)}")
        return None

def extract_frames(video_path: str, interval: int = 1) -> List[Image.Image]:
    """Extract frames from video at specified intervals"""
    frames = []
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval)

    success = True
    count = 0
    while success:
        success, frame = video.read()
        if count % frame_interval == 0 and success:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            frames.append(pil_image)
        count += 1

    video.release()
    return frames

def analyze_video_content(model, frames: List[Image.Image], ad_text: str) -> Dict:
    """Analyze video content using Gemini"""
    prompt = f"""
    Analyze this video advertisement and provide:
    1. Scene-by-scene breakdown (timestamp + description)
    2. Key messaging elements and hooks
    3. Visual techniques and production elements used
    4. Target audience analysis
    5. Call-to-action effectiveness
    6. Unique selling propositions
    7. Brand voice and tone analysis

    Ad Text: {ad_text}

    Focus on actionable insights while avoiding direct replication.
    """

    try:
        response = model.generate_content([prompt] + frames)
        return response.text
    except Exception as e:
        st.error(f"Error analyzing video: {str(e)}")
        return None

def generate_competitive_insights(analysis: str) -> str:
    """Generate competitive insights based on analysis"""
    prompt = f"""
    Based on the following ad analysis, provide strategic recommendations:
    {analysis}

    Include:
    1. Key success factors and why they work
    2. Market positioning insights
    3. Production techniques breakdown
    4. Audience engagement strategies
    5. Differentiation opportunities
    6. Estimated production budget range
    7. Resource requirements (talent, location, props)

    Focus on strategic understanding rather than direct copying.
    """

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating insights: {str(e)}")
        return None

def main():
    st.title("Ad Creative Analysis Platform")
    st.write("Analyze competitor video ads for strategic insights")

    # Initialize Gemini
    if 'GOOGLE_API_KEY' not in st.session_state:
        api_key = st.text_input("Enter your Google API Key:", type="password")
        if api_key:
            genai.configure(api_key=api_key)
            st.session_state['GOOGLE_API_KEY'] = api_key
            st.success("API Key configured!")

    # Main interface
    if 'GOOGLE_API_KEY' in st.session_state:
        page_name = st.text_input("Enter Facebook Page Name (e.g., 'CocaCola'):")

        if st.button("Analyze Ads"):
            if page_name:
                with st.spinner("Fetching ads..."):
                    scraper = AdLibraryScraper()
                    try:
                        video_info = scraper.extract_video_urls(page_name)
                        scraper.close()

                        if not video_info:
                            st.warning("No video ads found. Try a different page or check the page name.")
                            return

                        # Process each video
                        for idx, video in enumerate(video_info):
                            st.subheader(f"Ad #{idx + 1}")

                            # Download video
                            temp_path = f"temp_video_{idx}.mp4"
                            video_path = download_video(video['url'], temp_path)

                            if video_path:
                                # Extract and analyze frames
                                frames = extract_frames(video_path)
                                model = genai.GenerativeModel('gemini-pro-vision')

                                # Analyze content
                                with st.spinner("Analyzing video content..."):
                                    analysis = analyze_video_content(model, frames, video['text'])

                                if analysis:
                                    st.write("### Analysis")
                                    st.write(analysis)

                                    # Generate competitive insights
                                    with st.spinner("Generating strategic insights..."):
                                        insights = generate_competitive_insights(analysis)

                                    if insights:
                                        st.write("### Strategic Recommendations")
                                        st.write(insights)

                                    # Export functionality
                                    export_data = {
                                        'timestamp': datetime.now().isoformat(),
                                        'page_name': page_name,
                                        'video_info': video,
                                        'analysis': analysis,
                                        'insights': insights
                                    }

                                    st.download_button(
                                        "Download Analysis",
                                        data=json.dumps(export_data, indent=2),
                                        file_name=f"ad_analysis_{idx}.json",
                                        mime="application/json"
                                    )

                                # Cleanup
                                try:
                                    os.remove(video_path)
                                except:
                                    pass

                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        if 'scraper' in locals():
                            scraper.close()

if __name__ == "__main__":
    main()
