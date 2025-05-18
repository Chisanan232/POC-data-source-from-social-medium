#!/usr/bin/env python3
"""
Batch Video Content Parser
This script provides functionality to process multiple video files in a directory.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
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
logger = logging.getLogger('batch_video_parser')


def process_video_file(video_path, output_dir, use_openai, openai_api_key):
    """
    Process a single video file.
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save output files
        use_openai (bool): Whether to use OpenAI for transcription
        openai_api_key (str): OpenAI API key
        
    Returns:
        dict: Processing result
    """
    try:
        video_name = Path(video_path).name
        logger.info(f"Processing video: {video_name}")
        
        parser = VideoContentParser(
            video_path=video_path,
            output_dir=output_dir,
            use_openai=use_openai,
            openai_api_key=openai_api_key
        )
        
        result = parser.process_video()
        
        return {
            "video_path": video_path,
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing {video_path}: {e}")
        return {
            "video_path": video_path,
            "success": False,
            "error": str(e)
        }


def main():
    """Main function to run the batch processing script."""
    parser = argparse.ArgumentParser(
        description='Batch process multiple video files to extract text content'
    )
    
    parser.add_argument(
        '--input-dir', '-i',
        required=True,
        help='Directory containing video files to process'
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
        '--max-workers', '-w',
        type=int,
        default=4,
        help='Maximum number of worker threads for parallel processing'
    )
    
    parser.add_argument(
        '--file-extensions', '-e',
        nargs='+',
        default=['mp4', 'mov', 'avi', 'mkv', 'webm'],
        help='Video file extensions to process'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get OpenAI API key from args or environment
    openai_api_key = args.openai_api_key or os.environ.get('OPENAI_API_KEY')
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd() / 'video_output'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Find all video files in the input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        logger.error(f"Input directory not found: {args.input_dir}")
        return
    
    video_files = []
    for ext in args.file_extensions:
        video_files.extend(list(input_dir.glob(f"*.{ext}")))
    
    if not video_files:
        logger.error(f"No video files found in {args.input_dir}")
        return
    
    logger.info(f"Found {len(video_files)} video files to process")
    
    # Process videos in parallel
    results = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [
            executor.submit(
                process_video_file, 
                str(video_path), 
                str(output_dir), 
                args.use_openai, 
                openai_api_key
            ) 
            for video_path in video_files
        ]
        
        for future in futures:
            results.append(future.result())
    
    # Generate summary report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"batch_processing_report_{timestamp}.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== BATCH VIDEO PROCESSING REPORT ===\n\n")
        f.write(f"Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input directory: {args.input_dir}\n")
        f.write(f"Output directory: {output_dir}\n")
        f.write(f"Total videos processed: {len(results)}\n")
        f.write(f"Successful: {sum(1 for r in results if r['success'])}\n")
        f.write(f"Failed: {sum(1 for r in results if not r['success'])}\n\n")
        
        f.write("=== PROCESSING DETAILS ===\n\n")
        for i, result in enumerate(results, 1):
            video_name = Path(result['video_path']).name
            f.write(f"{i}. {video_name}: {'SUCCESS' if result['success'] else 'FAILED'}\n")
            
            if not result['success']:
                f.write(f"   Error: {result['error']}\n")
            else:
                if 'transcription' in result['result']:
                    f.write(f"   Transcription method: {result['result'].get('transcription_method', 'unknown')}\n")
                    f.write(f"   Transcription length: {len(result['result']['transcription'])} characters\n")
                
                if 'subtitles' in result['result'] and result['result']['subtitles']:
                    f.write(f"   Subtitles: {len(result['result']['subtitles'])} entries\n")
            
            f.write("\n")
    
    print(f"\nBatch processing complete!")
    print(f"Processed {len(results)} videos: {sum(1 for r in results if r['success'])} successful, {sum(1 for r in results if not r['success'])} failed")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
