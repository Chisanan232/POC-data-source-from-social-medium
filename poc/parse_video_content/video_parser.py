#!/usr/bin/env python3
"""
Video Content Parser Module
This module provides functionality to extract text content from videos,
including audio transcription and subtitle extraction.
"""

import os
import logging
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
import json
import re

# Third-party imports
import speech_recognition as sr
# We'll use subprocess to call ffmpeg directly instead of moviepy
# from moviepy.editor import VideoFileClip
from pydub import AudioSegment

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('video_content_parser')


class VideoContentParser:
    """Class to parse and extract text content from videos."""
    
    def __init__(self, video_path, output_dir=None, use_openai=False, openai_api_key=None):
        """
        Initialize the video content parser.
        
        Args:
            video_path (str): Path to the video file
            output_dir (str, optional): Directory to save output files
            use_openai (bool, optional): Whether to use OpenAI for transcription
            openai_api_key (str, optional): OpenAI API key for transcription
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.use_openai = use_openai
        self.openai_api_key = openai_api_key
        
        # Check if we have the required tools
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required external dependencies are installed."""
        try:
            # Check for ffmpeg
            subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("ffmpeg is not installed or not in PATH. Some features may not work.")
        
        # If using OpenAI, check for API key
        if self.use_openai and not self.openai_api_key:
            # Try to get from environment
            self.openai_api_key = os.environ.get('OPENAI_API_KEY')
            if not self.openai_api_key:
                logger.warning("OpenAI API key not provided. Falling back to local transcription.")
                self.use_openai = False
    
    def extract_audio(self, output_path=None):
        """
        Extract audio from the video file using ffmpeg directly.
        
        Args:
            output_path (str, optional): Path to save the audio file
            
        Returns:
            str: Path to the extracted audio file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"audio_{timestamp}.wav"
        
        try:
            logger.info(f"Extracting audio from {self.video_path}")
            
            # Use ffmpeg to extract audio
            cmd = [
                "ffmpeg",
                "-i", str(self.video_path),
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit little-endian audio codec
                "-ar", "44100",  # 44.1kHz sample rate
                "-ac", "2",  # 2 channels (stereo)
                "-y",  # Overwrite output file if it exists
                str(output_path)
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                logger.error(f"Error extracting audio: {process.stderr}")
                return None
            
            logger.info(f"Audio extracted successfully to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None
    
    def transcribe_audio_local(self, audio_path=None):
        """
        Transcribe audio using local speech recognition.
        
        Args:
            audio_path (str, optional): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        if not audio_path:
            audio_path = self.extract_audio()
            if not audio_path:
                return None
        
        try:
            logger.info(f"Transcribing audio using local speech recognition")
            recognizer = sr.Recognizer()
            
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
            
            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio_data)
            
            logger.info(f"Transcription completed successfully")
            return text
            
        except sr.UnknownValueError:
            logger.error("Speech recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from speech recognition service: {e}")
            return None
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    def transcribe_audio_openai(self, audio_path=None):
        """
        Transcribe audio using OpenAI's Whisper API.
        
        Args:
            audio_path (str, optional): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        if not audio_path:
            audio_path = self.extract_audio()
            if not audio_path:
                return None
        
        try:
            logger.info(f"Transcribing audio using OpenAI Whisper API")
            
            # Import OpenAI here to avoid dependency issues if not using it
            import openai
            
            # Set up OpenAI client
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            text = response
            
            logger.info(f"OpenAI transcription completed successfully")
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing with OpenAI: {e}")
            logger.info("Falling back to local transcription")
            return self.transcribe_audio_local(audio_path)
    
    def extract_subtitles(self):
        """
        Extract subtitles from the video file.
        
        Returns:
            dict: Dictionary containing subtitles data
        """
        try:
            logger.info(f"Extracting subtitles from {self.video_path}")
            
            # Create a temporary file for the subtitles
            with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as temp_file:
                temp_subtitle_path = temp_file.name
            
            # Extract subtitles using ffmpeg
            cmd = [
                "ffmpeg",
                "-i", str(self.video_path),
                "-map", "0:s:0",  # Select the first subtitle stream
                "-c", "copy",
                temp_subtitle_path
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Check if subtitles were extracted
            if process.returncode != 0:
                logger.warning("No embedded subtitles found in the video")
                
                # Try alternative method to extract any text streams
                logger.info("Trying alternative subtitle extraction method...")
                
                # Get video information
                probe_cmd = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_streams",
                    str(self.video_path)
                ]
                
                probe_result = subprocess.run(
                    probe_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if probe_result.returncode == 0:
                    video_info = json.loads(probe_result.stdout)
                    
                    # Look for subtitle streams
                    subtitle_streams = [
                        stream for stream in video_info.get('streams', [])
                        if stream.get('codec_type') == 'subtitle'
                    ]
                    
                    if subtitle_streams:
                        logger.info(f"Found {len(subtitle_streams)} subtitle streams")
                        
                        # Try to extract each subtitle stream
                        for i, stream in enumerate(subtitle_streams):
                            stream_index = stream.get('index')
                            
                            extract_cmd = [
                                "ffmpeg",
                                "-i", str(self.video_path),
                                "-map", f"0:{stream_index}",
                                "-c", "copy",
                                f"{temp_subtitle_path}_{i}"
                            ]
                            
                            subprocess.run(
                                extract_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                    else:
                        logger.warning("No subtitle streams found in the video")
                
                # If no embedded subtitles, return None
                return None
            
            # Parse the SRT file
            subtitles = self._parse_srt(temp_subtitle_path)
            
            # Clean up the temporary file
            os.unlink(temp_subtitle_path)
            
            logger.info(f"Subtitles extracted successfully")
            return subtitles
            
        except Exception as e:
            logger.error(f"Error extracting subtitles: {e}")
            return None
    
    def _parse_srt(self, srt_path):
        """
        Parse an SRT subtitle file.
        
        Args:
            srt_path (str): Path to the SRT file
            
        Returns:
            list: List of subtitle entries with timestamps and text
        """
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regular expression to parse SRT format
            pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\n\d+|\Z)'
            matches = re.findall(pattern, content)
            
            subtitles = []
            for match in matches:
                index, start_time, end_time, text = match
                subtitles.append({
                    'index': int(index),
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text.strip()
                })
            
            return subtitles
            
        except Exception as e:
            logger.error(f"Error parsing SRT file: {e}")
            return None
    
    def process_video(self):
        """
        Process the video to extract all available text content.
        
        Returns:
            dict: Dictionary containing all extracted content
        """
        result = {
            "video_path": str(self.video_path),
            "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Extract audio and transcribe
        audio_path = self.extract_audio()
        
        if audio_path:
            if self.use_openai and self.openai_api_key:
                transcription = self.transcribe_audio_openai(audio_path)
                result["transcription"] = transcription
                result["transcription_method"] = "openai"
            else:
                transcription = self.transcribe_audio_local(audio_path)
                result["transcription"] = transcription
                result["transcription_method"] = "local"
        
        # Extract subtitles
        subtitles = self.extract_subtitles()
        result["subtitles"] = subtitles
        
        if subtitles:
            # Combine all subtitle text
            subtitle_text = "\n".join([item["text"] for item in subtitles])
            result["subtitle_text"] = subtitle_text
        
        # Save results to files
        self._save_results(result)
        
        return result
    
    def _save_results(self, result):
        """
        Save the results to a JSON file and a text-only file.
        
        Args:
            result (dict): Dictionary containing the results
        """
        # Save the results to a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"video_content_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Video content extraction results saved to {output_path}")
        
        # Also save a text-only version for convenience
        text_output_path = self.output_dir / f"video_text_{timestamp}.txt"
        
        with open(text_output_path, 'w', encoding='utf-8') as f:
            f.write("=== VIDEO CONTENT EXTRACTION ===\n\n")
            f.write(f"Video: {self.video_path}\n")
            f.write(f"Processed: {result['processing_time']}\n\n")
            
            if result['transcription']:
                f.write("=== TRANSCRIPTION ===\n")
                f.write(f"Method: {result['transcription_method']}\n\n")
                f.write(result['transcription'])
                f.write("\n\n")
            
            if result['subtitles']:
                f.write("=== SUBTITLES ===\n\n")
                for item in result['subtitles']:
                    f.write(f"[{item['start_time']} --> {item['end_time']}]\n")
                    f.write(f"{item['text']}\n\n")
        
        logger.info(f"Text-only content saved to {text_output_path}")


def segment_long_audio(audio_path, segment_length_ms=60000):
    """
    Segment a long audio file into smaller chunks for better transcription.
    
    Args:
        audio_path (str): Path to the audio file
        segment_length_ms (int): Length of each segment in milliseconds
        
    Returns:
        list: List of paths to the segmented audio files
    """
    try:
        logger.info(f"Segmenting audio file: {audio_path}")
        
        # Load the audio file
        audio = AudioSegment.from_file(audio_path)
        
        # Calculate the number of segments
        duration_ms = len(audio)
        num_segments = (duration_ms // segment_length_ms) + (1 if duration_ms % segment_length_ms > 0 else 0)
        
        logger.info(f"Audio duration: {duration_ms}ms, creating {num_segments} segments")
        
        # Create a directory for the segments
        output_dir = Path(audio_path).parent / "segments"
        output_dir.mkdir(exist_ok=True)
        
        # Split the audio into segments
        segment_paths = []
        for i in range(num_segments):
            start_ms = i * segment_length_ms
            end_ms = min((i + 1) * segment_length_ms, duration_ms)
            
            segment = audio[start_ms:end_ms]
            segment_path = output_dir / f"segment_{i:03d}.wav"
            segment.export(str(segment_path), format="wav")
            
            segment_paths.append(str(segment_path))
            
        logger.info(f"Created {len(segment_paths)} audio segments")
        return segment_paths
        
    except Exception as e:
        logger.error(f"Error segmenting audio: {e}")
        return None
