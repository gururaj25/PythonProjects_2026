# Audio Transcription with OpenAI Whisper

This Python script uses OpenAI's Whisper API to transcribe audio files in regional languages like Hindi or Kannada, and optionally translates the transcription to English.

## Prerequisites

1. **Python 3:** Ensure Python 3 is installed.
2. **Required Libraries:** Install the necessary libraries using pip:
   ```bash
   pip install requests pydub
   ```
3. **OpenAI API Key:** You must have an OpenAI API key to use this script.
   - Set it as an environment variable before running the script:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

## Script: `transcribe_whisper.py`

The script `transcribe_whisper.py` performs the transcription using OpenAI's Whisper API and optionally translates the result to English.

## Usage

Run the script from your terminal using the following command structure:

```bash
python transcribe_whisper.py <audio_file_path> <transcription_output_path> <translation_output_path> [--language <language_code>] [--translate]
```

**Arguments:**

1. `<audio_file_path>`: The full path to the input audio file (e.g., `/path/to/your/audio.mp3`).
2. `<transcription_output_path>`: The full path where the transcription text file will be saved.
3. `<translation_output_path>`: The full path where the English translation text file will be saved (if translation is enabled).

**Optional Arguments:**

- `--language <language_code>`: Specify the language code for transcription (e.g., 'hi' for Hindi, 'kn' for Kannada). If not provided, Whisper will auto-detect the language.
- `--translate`: Enable translation to English. If not specified, only transcription will be performed.

**Example:**

To transcribe a Hindi audio file and save the transcription without translation:

```bash
python transcribe_whisper.py hindi_speech.mp3 hindi_transcription.txt english_translation.txt --language hi
```

To transcribe and also translate to English:

```bash
python transcribe_whisper.py hindi_speech.mp3 hindi_transcription.txt english_translation.txt --language hi --translate
```

## Features

- **Large File Handling**: Automatically compresses audio files larger than 25MB to meet API limits.
- **Language Detection**: Can auto-detect the language if not specified.
- **Optional Translation**: Can translate the transcribed text to English if requested.

## Notes

- The script requires an internet connection to access the OpenAI API.
- OpenAI's Whisper API has a file size limit of 25MB. The script will attempt to compress larger files.
- The quality of transcription depends on the audio clarity and the language model's capabilities.
- Translation uses OpenAI's GPT model for high-quality results.
