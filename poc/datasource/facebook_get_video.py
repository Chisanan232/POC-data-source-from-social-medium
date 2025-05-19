#!/usr/bin/env python3
"""
Facebook Reel Video Downloader and Content Extractor
This script downloads a video from a Facebook reel URL using yt-dlp
and extracts the post text content.
"""

import os
import argparse
import subprocess
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime


def check_yt_dlp_installed():
    """Check if yt-dlp is installed in the system."""
    try:
        subprocess.run(["yt-dlp", "--version"],
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def install_yt_dlp():
    """Install yt-dlp using pip."""
    print("yt-dlp is not installed. Installing...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"],
                      check=True)
        print("yt-dlp installed successfully.")
        return True
    except subprocess.SubprocessError as e:
        print(f"Failed to install yt-dlp: {e}")
        return False


class FacebookContentExtractor:
    """Class to extract text content from Facebook posts."""
    
    def __init__(self, url):
        """Initialize with the Facebook URL."""
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def _get_mobile_url(self):
        """Convert URL to mobile version which is easier to scrape."""
        if 'www.facebook.com' in self.url:
            return self.url.replace('www.facebook.com', 'm.facebook.com')
        return self.url
    
    def extract_post_text(self):
        """Extract the text content from the Facebook post."""
        try:
            # Try with mobile URL first as it's usually easier to scrape
            mobile_url = self._get_mobile_url()
            print(f"Fetching post content from: {mobile_url}")
            
            response = self.session.get(mobile_url, timeout=30)
            if response.status_code != 200:
                print(f"Failed with mobile URL, trying original URL: {self.url}")
                response = self.session.get(self.url, timeout=30)
            
            if response.status_code != 200:
                print(f"Failed to fetch the page. Status code: {response.status_code}")
                return None
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different selectors that might contain post text
            # For mobile site
            post_text = None
            
            # Try to find the post text in the mobile version
            div_content = soup.find('div', {'data-ft': re.compile(r'.*')})
            if div_content and div_content.get_text().strip():
                post_text = div_content.get_text().strip()
            
            # Try meta description which often contains the post text
            if not post_text:
                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc and 'content' in meta_desc.attrs:
                    post_text = meta_desc['content'].strip()
            
            # Try og:description which also often contains the post text
            if not post_text:
                og_desc = soup.find('meta', {'property': 'og:description'})
                if og_desc and 'content' in og_desc.attrs:
                    post_text = og_desc['content'].strip()
            
            # Try to find text in any div with specific class patterns common in Facebook
            if not post_text:
                for div in soup.find_all('div', {'class': re.compile(r'(text|content|message|caption)')}):
                    if div.get_text().strip() and len(div.get_text().strip()) > 20:  # Avoid short texts
                        post_text = div.get_text().strip()
                        break
            
            # If we still don't have text, try to get it from the yt-dlp info
            if not post_text:
                print("Trying to extract text from video metadata...")
                info = self.get_video_info_with_ytdlp()
                if info and 'description' in info and info['description']:
                    post_text = info['description']
            
            if post_text:
                # Clean up the text (remove excessive whitespace, etc.)
                post_text = re.sub(r'\s+', ' ', post_text).strip()
                return post_text
            else:
                print("Could not extract post text content.")
                return None
            
        except Exception as e:
            print(f"Error extracting post text: {e}")
            return None
    
    def get_video_info_with_ytdlp(self):
        """Get video info using yt-dlp which might contain the description."""
        try:
            cmd = [
                "yt-dlp", 
                "--dump-json",
                "--no-playlist",
                self.url
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            if result.stdout:
                return json.loads(result.stdout)
            return None
        except subprocess.SubprocessError:
            return None


class FacebookVideoDownloader:
    """Class to download videos from Facebook using yt-dlp."""

    def __init__(self, url):
        """Initialize with the Facebook URL."""
        self.url = url

    def get_video_info(self):
        """Get information about the video without downloading it."""
        try:
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-playlist",
                self.url
            ]

            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

            if result.stdout:
                return json.loads(result.stdout)
            return None
        except subprocess.SubprocessError as e:
            print(f"Error getting video info: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return None

    def download_video(self, output_path=None):
        """Download the video using yt-dlp."""
        try:
            # Generate a filename if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"facebook_reel_{timestamp}.mp4"

            # Prepare the yt-dlp command
            cmd = [
                "yt-dlp",
                "--no-playlist",
                "-f", "best",  # Download best quality
                "-o", output_path,
                self.url
            ]

            print(f"Running command: {' '.join(cmd)}")

            # Run the command and stream output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Print output in real-time
            for line in process.stdout:
                print(line, end='')

            # Wait for the process to complete
            return_code = process.wait()

            if return_code == 0:
                print(f"\nVideo successfully downloaded to {output_path}")
                return True
            else:
                print(f"\nFailed to download video (return code: {return_code})")
                return False

        except subprocess.SubprocessError as e:
            print(f"Error downloading video: {e}")
            return False


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Download a video and extract text from a Facebook reel.')
    parser.add_argument('--url', type=str, default="https://www.facebook.com/reel/9323832897735854",
                        help='URL of the Facebook reel')
    parser.add_argument('--output', type=str, default=None,
                        help='Output path for the downloaded video')
    parser.add_argument('--info-only', action='store_true',
                        help='Only show video information without downloading')
    parser.add_argument('--text-only', action='store_true',
                        help='Only extract and show the post text without downloading the video')

    args = parser.parse_args()

    # Extract post text content first
    content_extractor = FacebookContentExtractor(args.url)
    post_text = content_extractor.extract_post_text()
    
    if post_text:
        print("\n" + "="*50)
        print("POST TEXT CONTENT:")
        print("="*50)
        print(post_text)
        print("="*50 + "\n")
    else:
        print("\nNo post text content found or could not be extracted.\n")

    # If text-only mode, exit here
    if args.text_only:
        return

    # Check if yt-dlp is installed
    if not check_yt_dlp_installed():
        if not install_yt_dlp():
            print("Please install yt-dlp manually: pip install yt-dlp")
            return

    downloader = FacebookVideoDownloader(args.url)

    if args.info_only:
        info = downloader.get_video_info()
        if info:
            print(json.dumps(info, indent=2))
        else:
            print("Failed to get video information.")
    else:
        downloader.download_video(args.output)


if __name__ == "__main__":
    main()
