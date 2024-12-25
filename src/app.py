from dotenv import load_dotenv
load_dotenv()

import os
import ssl
import certifi
import time
import streamlit as st
import google.generativeai as genai
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import random

# Configure SSL context
ssl._create_default_https_context = ssl._create_unverified_context

# Configure page
st.set_page_config(
    page_title="FB Ads Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def setup_driver():
    """Setup undetected-chromedriver with automatic version detection"""
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    try:
        driver = uc.Chrome(
            options=options,
            suppress_welcome=True,
            use_subprocess=True
        )
        return driver
    except Exception as e:
        st.error(f"Failed to initialize browser: {str(e)}")
        st.error("Detailed error info:", exc_info=True)
        return None

def extract_ads(driver, url):
    """Extract ads using undetected-chromedriver"""
    ads_data = []

    try:
        # Load the page
        driver.get(url)
        time.sleep(5)  # Initial load

        # Simulate human-like scrolling
        for _ in range(5):
            scroll_amount = random.randint(300, 700)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(2, 4))

        # Find all ad containers
        ad_containers = driver.find_elements(By.CSS_SELECTOR, '[role="article"]')
        st.write(f"Found {len(ad_containers)} potential ad containers")

        for container in ad_containers:
            try:
                # Find video elements or play buttons
                videos = container.find_elements(By.TAG_NAME, "video")
                play_buttons = container.find_elements(By.CSS_SELECTOR, '[aria-label*="Play"]')

                if videos or play_buttons:
                    # Extract ad text
                    text_elements = container.find_elements(By.CSS_SELECTOR, '[dir="auto"]')
                    ad_text = ' '.join([elem.text for elem in text_elements if elem.text])

                    # Get video URL
                    video_url = None
                    if videos:
                        video_url = videos[0].get_attribute("src")
                    elif play_buttons:
                        driver.execute_script("arguments[0].click();", play_buttons[0])
                        time.sleep(1)
                        video = container.find_element(By.TAG_NAME, "video")
                        video_url = video.get_attribute("src")

                    if video_url:
                        # Get ad metadata
                        date_element = container.find_elements(By.CSS_SELECTOR, "span[style*='color: rgb(101, 103, 107)']")
                        start_date = date_element[0].text if date_element else "Date not found"

                        ads_data.append({
                            "video_url": video_url,
                            "ad_text": ad_text.strip(),
                            "start_date": start_date
                        })
                        st.write(f"Found video ad with start date: {start_date}")

            except Exception as e:
                st.warning(f"Error processing ad container: {str(e)}")
                continue

        return ads_data

    except Exception as e:
        st.error(f"Error extracting ads: {str(e)}")
        return []

def analyze_ad_with_gemini(video_url, ad_text):
    """Analyze ad using Gemini"""
    prompt = f"""
    Analyze this Facebook video ad:

    Ad Text: {ad_text}
    Video URL: {video_url}

    Provide a detailed analysis including:
    1. Key messaging and hooks used
    2. Target audience analysis
    3. Call-to-action effectiveness
    4. Visual techniques employed
    5. Unique selling propositions
    6. Competitive strategy insights
    7. Estimated production approach

    Format your response in clear sections.
    """

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing ad: {str(e)}"

def main():
    st.title("Facebook Video Ad Analyzer")

    # Sidebar for API key
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input(
            "Google API Key:",
            type="password",
            value=os.getenv('GOOGLE_API_KEY', '')
        )
        if api_key:
            os.environ['GOOGLE_API_KEY'] = api_key
            genai.configure(api_key=api_key)
            st.success("✅ API Key configured")

    if not api_key:
        st.warning("⚠️ Please enter your Google API Key to begin")
        return

    # Main interface
    st.write("Enter a Facebook Ad Library URL to analyze video ads")

    # URL input
    fb_url = st.text_input(
        "Facebook Ad Library URL:",
        placeholder="https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&view_all_page_id=..."
    )

    if st.button("🔍 Analyze Ads", type="primary"):
        if not fb_url:
            st.warning("Please enter a Facebook Ad Library URL")
            return

        try:
            with st.spinner("Initializing browser..."):
                driver = setup_driver()

                if driver:
                    with st.spinner("Extracting ads (this may take a minute)..."):
                        ads_data = extract_ads(driver, fb_url)

                        if ads_data:
                            st.success(f"Found {len(ads_data)} video ads!")

                            for i, ad in enumerate(ads_data, 1):
                                with st.expander(f"🎥 Ad #{i} - {ad['start_date']}"):
                                    col1, col2 = st.columns([1, 1])

                                    with col1:
                                        st.subheader("Ad Content")
                                        st.write("**Ad Text:**")
                                        st.write(ad['ad_text'])

                                        if ad['video_url']:
                                            st.write("**Video:**")
                                            st.video(ad['video_url'])

                                    with col2:
                                        st.subheader("Analysis")
                                        with st.spinner("Analyzing ad..."):
                                            analysis = analyze_ad_with_gemini(
                                                ad['video_url'],
                                                ad['ad_text']
                                            )
                                            st.write(analysis)

                                    # Export option
                                    export_data = {
                                        'ad_content': ad,
                                        'analysis': analysis
                                    }

                                    st.download_button(
                                        "📥 Download Analysis",
                                        data=json.dumps(export_data, indent=2),
                                        file_name=f"ad_analysis_{i}.json",
                                        mime="application/json"
                                    )

                        else:
                            st.warning("No video ads found. Try:")
                            st.write("1. Checking if the page has active video ads")
                            st.write("2. Refreshing the page and trying again")
                            st.write("3. Using a different Facebook page")

                    driver.quit()

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
