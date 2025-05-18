#!/usr/bin/env python3
"""
Video Content Parser CLI
This script provides a command-line interface to extract text content from videos,
including audio transcription and subtitle extraction.
"""

import os
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to the path so we can import the video_parser module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from video_parser import VideoContentParser

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('video_parser_cli')


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description='Extract text content from videos, including transcription and subtitles'
    )
    
    parser.add_argument(
        '--video', '-v', 
        required=True,
        help='Path to the video file'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        help='Directory to save output files'
    )
    
    parser.add_argument(
        '--use-openai', '-ai',
        action='store_true',
        help='Use OpenAI Whisper API for transcription (requires API key)'
    )
    
    parser.add_argument(
        '--openai-api-key', '-k',
        help='OpenAI API key (if not provided in .env file)'
    )
    
    parser.add_argument(
        '--verbose', '-vb',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--extract-audio-only', '-a',
        action='store_true',
        help='Only extract audio from the video, without transcription'
    )
    
    parser.add_argument(
        '--extract-subtitles-only', '-s',
        action='store_true',
        help='Only extract subtitles from the video, without transcription'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get OpenAI API key from args or environment
    openai_api_key = args.openai_api_key or os.environ.get('OPENAI_API_KEY')
    
    try:
        # Create the video parser
        video_parser = VideoContentParser(
            video_path=args.video,
            output_dir=args.output_dir,
            use_openai=args.use_openai,
            openai_api_key=openai_api_key
        )
        
        print(f"Processing video: {args.video}")
        
        # Handle specific extraction modes
        if args.extract_audio_only:
            print("Extracting audio only...")
            audio_path = video_parser.extract_audio()
            if audio_path:
                print(f"Audio extracted successfully to: {audio_path}")
            else:
                print("Failed to extract audio")
            return
        
        if args.extract_subtitles_only:
            print("Extracting subtitles only...")
            subtitles = video_parser.extract_subtitles()
            if subtitles:
                print(f"Extracted {len(subtitles)} subtitle entries")
                
                # Save subtitles to a file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
                output_path = output_dir / f"subtitles_{timestamp}.txt"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    for item in subtitles:
                        f.write(f"[{item['start_time']} --> {item['end_time']}]\n")
                        f.write(f"{item['text']}\n\n")
                
                print(f"Subtitles saved to: {output_path}")
            else:
                print("No subtitles found in the video")
            return
        
        # Process the entire video
        print("Processing video content...")
        result = video_parser.process_video()
        
        # Print a summary of the results
        print("\n=== Video Content Extraction Summary ===")
        
        if result.get('transcription'):
            print(f"\nTranscription Method: {result.get('transcription_method', 'unknown')}")
            print(f"Transcription Length: {len(result['transcription'])} characters")
            print(f"Transcription Preview: {result['transcription'][:100]}...")
        else:
            print("\nNo transcription available")
        
        if result.get('subtitles'):
            print(f"\nSubtitles: {len(result['subtitles'])} entries")
            print(f"Subtitle Text Length: {len(result.get('subtitle_text', ''))} characters")
        else:
            print("\nNo subtitles available")
        
        print(f"\nResults saved to: {video_parser.output_dir}")
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
