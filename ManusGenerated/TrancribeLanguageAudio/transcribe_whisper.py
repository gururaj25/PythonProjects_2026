import os
import argparse
import requests
import json
import time
from pydub import AudioSegment

def transcribe_with_whisper(audio_path, language=None):
    """
    Transcribes audio using OpenAI's Whisper API.
    
    Args:
        audio_path (str): Path to the audio file.
        language (str): Optional language code (e.g., 'hi' for Hindi, 'kn' for Kannada).
                        If None, Whisper will auto-detect the language.
    
    Returns:
        str: The transcribed text, or None if transcription fails.
    """
    # Check if API key is set
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key with: export OPENAI_API_KEY='your-api-key'")
        return None
    
    # Check if file exists
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return None
    
    # Check file size and format
    try:
        file_size = os.path.getsize(audio_path) / (1024 * 1024)  # Size in MB
        print(f"Audio file size: {file_size:.2f} MB")
        
        if file_size > 25:
            print("Warning: File size exceeds 25 MB, which is the limit for the Whisper API.")
            print("Converting and compressing audio...")
            
            # Convert to MP3 with compression to reduce size
            temp_path = "temp_compressed_audio.mp3"
            audio = AudioSegment.from_file(audio_path)
            audio.export(temp_path, format="mp3", bitrate="64k")
            
            compressed_size = os.path.getsize(temp_path) / (1024 * 1024)
            print(f"Compressed file size: {compressed_size:.2f} MB")
            
            if compressed_size > 25:
                print("Error: Even after compression, file size exceeds 25 MB.")
                print("Please use a shorter audio clip or further compress the audio manually.")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
            
            audio_path = temp_path
    except Exception as e:
        print(f"Error checking file size: {e}")
        return None
    
    # Prepare API request
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # Prepare form data
    data = {"model": "whisper-1"}
    if language:
        data["language"] = language
    
    # Send request
    try:
        print(f"Sending audio to Whisper API for transcription...")
        with open(audio_path, "rb") as audio_file:
            files = {"file": audio_file}
            response = requests.post(url, headers=headers, data=data, files=files)
        
        # Clean up temporary file if created
        if audio_path == "temp_compressed_audio.mp3" and os.path.exists(audio_path):
            os.remove(audio_path)
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            print("Transcription successful.")
            return result.get("text")
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        # Clean up temporary file if created
        if audio_path == "temp_compressed_audio.mp3" and os.path.exists(audio_path):
            os.remove(audio_path)
        return None

def translate_text(text, target_language='en'):
    """
    Translates text using OpenAI's GPT model.
    
    Args:
        text (str): Text to translate.
        target_language (str): Target language (default: 'en' for English).
    
    Returns:
        str: Translated text, or None if translation fails.
    """
    if not text:
        print("No text provided for translation.")
        return None
    
    # Check if API key is set
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key with: export OPENAI_API_KEY='your-api-key'")
        return None
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare the prompt
    prompt = f"Translate the following text to {target_language}. Preserve the meaning, tone, and style as much as possible:\n\n{text}"
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    try:
        print(f"Translating text to {target_language}...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result["choices"][0]["message"]["content"].strip()
            print("Translation successful.")
            return translated_text
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred during translation: {e}")
        return None

def save_to_file(text, filename):
    """Saves the given text to a file."""
    if text is None:
        print(f"Cannot save None to {filename}. Skipping file write.")
        return
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to file {filename}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio in a regional language and translate to English using OpenAI APIs.")
    parser.add_argument("audio_file", help="Path to the input audio file.")
    parser.add_argument("--language", help="Language code for transcription (e.g., 'hi' for Hindi, 'kn' for Kannada). If not provided, language will be auto-detected.")
    parser.add_argument("transcription_output", help="Path to save the transcription file.")
    parser.add_argument("translation_output", help="Path to save the English translation file.")
    parser.add_argument("--translate", action="store_true", help="Enable translation to English (requires additional API calls).")
    
    args = parser.parse_args()
    
    print(f"--- Starting process for {args.audio_file} ---")
    if args.language:
        print(f"Language: {args.language}")
    else:
        print("Language: Auto-detect")
    print(f"Transcription output: {args.transcription_output}")
    print(f"Translation output: {args.translation_output}")
    print(f"Translation enabled: {args.translate}")
    
    # Transcription
    transcribed_text = transcribe_with_whisper(args.audio_file, args.language)
    
    if transcribed_text is not None:
        save_to_file(transcribed_text, args.transcription_output)
        
        # Translation (if enabled)
        if args.translate:
            translated_text = translate_text(transcribed_text)
            if translated_text is not None:
                save_to_file(translated_text, args.translation_output)
            else:
                print("Skipping saving translation due to translation error.")
        else:
            print("Translation skipped (not enabled).")
    else:
        print("Skipping translation and saving due to transcription error.")
    
    print("--- Processing finished. ---")

if __name__ == "__main__":
    main()
