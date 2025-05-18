#!/usr/bin/env python3
"""
Facebook Reel Video Downloader
This script downloads a video from a Facebook reel URL using yt-dlp.
"""

import os
import argparse
import subprocess
import sys
import json
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
    parser = argparse.ArgumentParser(description='Download a video from a Facebook reel.')
    parser.add_argument('--url', type=str, default="https://www.facebook.com/reel/9323832897735854",
                        help='URL of the Facebook reel')
    parser.add_argument('--output', type=str, default=None,
                        help='Output path for the downloaded video')
    parser.add_argument('--info-only', action='store_true',
                        help='Only show video information without downloading')

    args = parser.parse_args()

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
