"""
Program Name: transcribe_audio.py
Author: DarkRook Cyber, LLC
Description: 
    - Note: This Python script will need alotta help to run on a Mac, and will only take a .wav file as input. Will run fine on a Linux machine. But fear not see steps below to get this script to run on MacOs!
    - make sure you have python3 on your Mac, open a Terminal window
    - Install Homebrew: 
         /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    - Install flac: 
         brew install flac
    - Install ffmpeg: 
         brew install ffmpeg
    - Install Google's Speech Recognition API: 
         pip3 install SpeechRecognition
    - Install PyDub: 
         pip3 install pydub
    - clean up the input .wav file to work with Google's API (Google's API is picky and wants the PCM 16-bit audio codec which is "pcm_s16le" and 16,000Hz): 
         ffmpeg -i path/to/your/input_audio_file.wav -acodec pcm_s16le -ar 16000 path/to/your/output_audio_file.wav
    - Run the script (assuming local path to script and inout audio file):
         python3 transcribe_audio.py output.wav script.txt
    -  Note: This script will generate little 30 second temporary audio files, to break up the original audio file into chunks for analysis via Google's API. Google's free version only analyzes for about 30-60 seconds of audio before timing out. Have tried other methods of chunking within the script, but the most reliable way was to use PyDub to create new audio files and use those as the chunks. If you can find a better way to do this with free Google'ness to do the speech to text transcription, please let me know!  
License:
    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

Note:
    For questions/comments please contact darkrookcyber@gmail.com
"""

#includes
import argparse
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import detect_nonsilent


# void transcribe_audio(*audioFile, *outputFile)
def transcribe_audio(audio_file_path, output_file_name):
    recognizer = sr.Recognizer()
    chunk_length = 30 * 1000  # Duration of each chunk in milliseconds for pydub
    overlap = 2 * 1000  # Overlap duration in milliseconds for pydub

    with sr.AudioFile(audio_file_path) as source:
        audio = recognizer.record(source)  # Record the entire file

    # Convert AudioData to an AudioSegment
    audio_segment = AudioSegment(
        data=audio.get_raw_data(), 
        sample_width=audio.sample_width, 
        frame_rate=audio.sample_rate,
        channels=1
    )

    chunks = [audio_segment[i:i + chunk_length] for i in range(0, len(audio_segment), chunk_length - overlap)]

    with open(output_file_name, 'w') as file:
        for i, chunk in enumerate(chunks):
            nonsilent_ranges = detect_nonsilent(chunk, min_silence_len=1000, silence_thresh=chunk.dBFS-14)

            if not nonsilent_ranges:  # If the chunk is silent, skip it
                print(f"Skipping silent chunk {i+1}.")
                continue

            # Save the chunk to a temporary file
            temp_file = f"temp_chunk_{i+1}.wav"
            chunk.export(temp_file, format="wav")

            # Use the recognizer on the temporary file
            with sr.AudioFile(temp_file) as temp_source:
                temp_audio = recognizer.record(temp_source)

                try:
                    text = recognizer.recognize_google(temp_audio)
                    print(f"Chunk {i+1} transcription: {text}")
                    file.write(text + "\n")
                except sr.UnknownValueError:
                    print(f"Google Web Speech API could not understand chunk {i+1}.")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Web Speech API for chunk {i+1}; {e}")
                except Exception as e:
                    print(f"An unexpected error occurred in chunk {i+1}: {e}")
# end transcribe_audio()

        
        
# void main()
if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Transcribe an audio file to text.")
    parser.add_argument("audio_file", help="Path to the audio file to be transcribed.")
    parser.add_argument("output_file", help="Filename for the output text file.")

    # Parse command line arguments
    args = parser.parse_args()

    # Run the transcription function with the provided arguments
    transcribe_audio(args.audio_file, args.output_file)
# end main()