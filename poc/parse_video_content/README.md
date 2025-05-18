# Video Content Parser

This module provides functionality to extract text content from videos, including audio transcription and subtitle extraction.

## Features

- **Audio Extraction**: Extract audio tracks from video files
- **Speech Recognition**: Transcribe audio to text using local speech recognition
- **OpenAI Integration**: Optional transcription using OpenAI's Whisper API for higher accuracy
- **Subtitle Extraction**: Extract embedded subtitles from video files
- **Comprehensive Output**: Generate both JSON and text output files with all extracted content
- **Batch Processing**: Process multiple video files in parallel with a summary report

## Prerequisites

- Python 3.12 or higher
- FFmpeg installed on your system
- Poetry for dependency management

## Dependencies

The module uses the following Python libraries:
- `moviepy`: For video processing
- `pydub`: For audio processing
- `SpeechRecognition`: For local speech recognition
- `ffmpeg-python`: Python bindings for FFmpeg
- `openai`: For OpenAI Whisper API integration (optional)

## Installation

The dependencies are managed through Poetry. To install them:

```bash
poetry install
```

## Usage

### Command Line Interface

The module provides a command-line interface for easy usage:

```bash
# Basic usage
poetry run python poc/parse_video_content/parse_video.py --video /path/to/video.mp4

# Use OpenAI for transcription
poetry run python poc/parse_video_content/parse_video.py --video /path/to/video.mp4 --use-openai

# Specify output directory
poetry run python poc/parse_video_content/parse_video.py --video /path/to/video.mp4 --output-dir /path/to/output

# Extract audio only
poetry run python poc/parse_video_content/parse_video.py --video /path/to/video.mp4 --extract-audio-only

# Extract subtitles only
poetry run python poc/parse_video_content/parse_video.py --video /path/to/video.mp4 --extract-subtitles-only

# Enable verbose logging
poetry run python poc/parse_video_content/parse_video.py --video /path/to/video.mp4 --verbose
```

### Batch Processing

For processing multiple videos at once, use the batch processing script:

```bash
# Process all videos in a directory
poetry run python poc/parse_video_content/batch_process.py --input-dir /path/to/videos

# Use OpenAI for transcription
poetry run python poc/parse_video_content/batch_process.py --input-dir /path/to/videos --use-openai

# Specify output directory
poetry run python poc/parse_video_content/batch_process.py --input-dir /path/to/videos --output-dir /path/to/output

# Set the maximum number of parallel workers
poetry run python poc/parse_video_content/batch_process.py --input-dir /path/to/videos --max-workers 8

# Specify file extensions to process
poetry run python poc/parse_video_content/batch_process.py --input-dir /path/to/videos --file-extensions mp4 mov avi
```

### API Usage

You can also use the module programmatically in your Python code:

```python
from poc.parse_video_content.video_parser import VideoContentParser

# Create a parser instance
parser = VideoContentParser(
    video_path="/path/to/video.mp4",
    output_dir="/path/to/output",
    use_openai=True,  # Optional
    openai_api_key="your-api-key"  # Optional
)

# Process the video
result = parser.process_video()

# Or use individual methods
audio_path = parser.extract_audio()
transcription = parser.transcribe_audio_local(audio_path)
subtitles = parser.extract_subtitles()
```

## Output

The module generates two types of output files:

1. **JSON file** (`video_content_YYYYMMDD_HHMMSS.json`): Contains all extracted data in a structured format
2. **Text file** (`video_text_YYYYMMDD_HHMMSS.txt`): Contains the transcription and subtitles in a human-readable format

## OpenAI Integration

To use the OpenAI Whisper API for transcription:

1. Set your OpenAI API key in the `.env` file:
   ```
   OPENAI_API_KEY=your-api-key
   ```

2. Or pass it directly via the command line:
   ```bash
   poetry run python poc/parse_video_content/parse_video.py --video /path/to/video.mp4 --use-openai --openai-api-key your-api-key
   ```

## Notes

- For long videos, the local speech recognition might be less accurate. Consider using the OpenAI option for better results.
- The module attempts to extract subtitles in various formats, but not all video files contain embedded subtitles.
- If both transcription and subtitles are available, both will be included in the output.
