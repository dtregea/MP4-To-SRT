import moviepy.editor as mp
from pydub import AudioSegment
import speech_recognition as sr
import os
import argparse

# Get audio file
def extract_audio_from_video(video_path, audio_path):
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)


# Split audio file into chunks
def split_audio(audio_path, chunk_length_ms):
    audio = AudioSegment.from_file(audio_path)
    return [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]


# Perform the speech recognition on an audio chunk
def recognize_speech(audio_chunk, recognizer, language="ja-JP"):
    with sr.AudioFile(audio_chunk) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return ""


# Main function to generate SRT File
def create_subtitles(video_path, chunk_length_ms=10000, language="ja-JP"):
    audio_path = "temp_audio.wav"
    extract_audio_from_video(video_path, audio_path)

    audio_chunks = split_audio(audio_path, chunk_length_ms)
    recognizer = sr.Recognizer()

    subs = []
    print("Creating subtitle file")
    for i, chunk in enumerate(audio_chunks):
        print(f'{((i / len(audio_chunks)) * 100):.2f}%')
        chunk_path = f"chunk{i}.wav"
        chunk.export(chunk_path, format="wav")

        text = recognize_speech(chunk_path, recognizer, language)
        if text:
            start_time = i * (chunk_length_ms // 1000)
            end_time = start_time + (chunk_length_ms // 1000)
            subs.append((start_time, end_time, text))

        os.remove(chunk_path)

    os.remove(audio_path)

    srt_path = os.path.splitext(video_path)[0] + ".srt"
    with open(srt_path, 'w', encoding='utf-8') as srt_file:
        for i, (start, end, text) in enumerate(subs):
            srt_file.write(f"{i + 1}\n")
            srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
            srt_file.write(f"{text}\n\n")


# Format time for SRT
def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02},000"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate subtitles for a video file.")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("chunk_length_ms", type=int, default=5000, help="Length of each audio chunk in milliseconds")
    parser.add_argument("language", type=str, default="ja-JP", help="Language code for speech recognition")

    args = parser.parse_args()
    create_subtitles(args.video_path, args.chunk_length_ms, args.language)
    print("SRT File Created")
