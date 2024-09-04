import whisper
from datetime import timedelta
from srt import Subtitle
from deep_translator import GoogleTranslator
import srt
import json
import gradio as gr
import os
import random
import string
import re


# Insert a line break when the number of characters in a line reaches 21.
def add_line(s):
    new_s = ""
    line_len = 0
    for char in s:
        if line_len >= 21 and char == " ":
            new_s += "\n"
            line_len = 0
        else:
            new_s += char
            line_len += 1
    return new_s

    
# Embed subtitles in videos
def embed_subtitles(result_folder_path):
    # Convert SRT file to ASS file
    os.system(f"ffmpeg -i {result_folder_path}/target.srt {result_folder_path}/target.ass")

    with open(f"{result_folder_path}/target.ass", 'r') as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if 'Style: Default' in lines[i]:
            # change fontname, fontsize, and boldness
            fontname = "MS Gothic"
            fontsize = 20
            boldness = -1   #-1(Bold) or 0
            lines[i] = f'Style: Default,{fontname},{fontsize},&Hffffff,&Hffffff,&H0,&H0,{boldness},0,0,0,100,100,0,0,1,1,0,2,10,10,10,0\n'
            break

    with open(f"{result_folder_path}/target.ass", 'w') as f:
        f.writelines(lines)

    # Embed subtitles in video
    os.system(f"ffmpeg -i {result_folder_path}/target.mp4 -vf ass={result_folder_path}/target.ass {result_folder_path}/output.mp4")

# Use GoogleTranslator module to translate text into Japanese
def translate(text, translated_lang):
    translated = GoogleTranslator(source = 'auto',target = translated_lang).translate(text)
    return translated

# Download the video from the given YouTube URL.
def yt_download(URL, result_folder_path):
    path = f"{result_folder_path}/target.mp4"
    if not os.path.exists(path):
        print(f"Downloading video from {URL} to {path}")
        os.system(f"yt-dlp -f best -v {URL} -o {path}")
    else:
        print(f"Video already exists at {path}, skipping download.")

# Generate subtitles.
def generate_subtitles(result, result_folder_path, translated_lang):
    segments = result["segments"]
    subs = []

    # Iterate over the segments and create SRT subtitles for each segment.
    for data in segments:
        index = data["id"] + 1
        start = data["start"]
        end = data["end"]
        # Translate the segment text to the desired language.
        translated_text = translate(data["text"], translated_lang)

        # Add line breaks to the translated text to improve readability.
        text = add_line(translated_text)

        # Create an SRT subtitle object.
        sub = Subtitle(index = 1, start = timedelta(seconds = timedelta(seconds = start).seconds,
                                                microseconds = timedelta(seconds = start).microseconds),
                    end = timedelta(seconds = timedelta(seconds = end).seconds,
                                    microseconds = timedelta(seconds = end).microseconds), content = text, proprietary = '')

        # Append the subtitle to the list of subtitles.
        subs.append(sub)
    
    # Write the SRT file to disk.
    with open(result_folder_path + "/target.srt", mode = "w", encoding = "utf-8") as f:
        f.write(srt.compose(subs))

    return srt.compose(subs)

def generate_random_dir_name(length=8):
    letters = string.ascii_letters  # Use both uppercase and lowercase letters
    return ''.join(random.choice(letters) for i in range(length))

def init_gradle():
    with gr.Blocks() as app:
        gr.Markdown("### Create subtitles for a YouTube video.")
        
        with gr.Row():
            with gr.Column():
                yt_url = gr.Textbox(lines=2, label="Enter the YouTube URL",value="https://www.youtube.com/watch?v=8nG7z7x4t3A")
                translated_lang = gr.Dropdown(["english", "japanese", "french", "german", "spanish"], label="Translated Language", value="english")
                embed_subs = gr.Checkbox(label="Embed Subtitles", value=False)

            with gr.Column():
                log_output = gr.Textbox(lines=20, label="Logs", value="", interactive=False)

        submit_button = gr.Button(value="Create Subtitles")
        download_button = gr.File(label="Download Subtitles")
        subtitles = gr.Textbox(lines=10, label="Subtitles", value="")

        submit_button.click(
            fn=create_subtitles,
            inputs=[yt_url, translated_lang, embed_subs],
            outputs=[subtitles, log_output, download_button]
        )
    return app

def extract_video_id(yt_url):
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', yt_url)
    if video_id_match:
        return video_id_match.group(1)
    return None

def create_subtitles(yt_url, translated_lang, embed_subs):

    try:
        logs = []
        def log(message):
            logs.append(message)
            return "\n".join(logs)
        video_id = extract_video_id(yt_url)
        result_folder_path = f"./result/{video_id}"

        print(f"Extracted video ID: {video_id}")
        log(f"Creating subtitles for YouTube video: {yt_url} (ID: {video_id})")
        logs.append("Creating subtitles for YouTube video: {}".format(yt_url))
        if not os.path.exists(result_folder_path):
            os.makedirs(result_folder_path)

        yt_download(yt_url, result_folder_path)


        result_file_path = f"{result_folder_path}/result.json"

        if not os.path.exists(result_file_path):
            gr.Info("Transcribing video...")
            model = whisper.load_model("medium")
            result = model.transcribe(f"{result_folder_path}/target.mp4")
            gr.Info("Transcription completed.")
            with open(result_file_path, mode="w") as f:
                json.dump(result, f)
        else:
            log("Transcription already exists. Loading from file.")
            with open(result_file_path, mode="r") as f:
                result = json.load(f)
        log(f"Saving subtitles to SRT file...")
        print("Saving subtitles to SRT file...")
        srt_file_path = f"{result_folder_path}/target.srt"
        if not os.path.exists(srt_file_path):
            gr.Info("Generating subtitles...")
            subtitles = generate_subtitles(result, result_folder_path, translated_lang)
            gr.Info("Saving subtitles to SRT file...")
            with open(srt_file_path, mode="w") as f:
                f.write(subtitles)
        else:
            log("Subtitles already exist. Skipping generation.")
            with open(srt_file_path, mode="r") as f:
                subtitles = f.read()
            
        if embed_subs:
            log(f"Embedding subtitles into video...")
            embed_subtitles(result_folder_path)
            log(f"Subtitles embedded into video.")

        return subtitles, log("Process completed."), srt_file_path
    except Exception as e:
        return None, log(f"Error: {e}"), None
def main():
    app = init_gradle()
    # URL = input("Enter the YouTube URL to which you want to add subtitles:")
    # translated_lang = "english"
    # # translated_lang = input("Please enter the subtitle language (language after translation):")
    # result_folder_name = "out"
    # # result_folder_name = str(input("Specify the name of the folder in which to save the output results:"))

    # # Folder name to save output results
    # result_folder_path = f"./result/{result_folder_name}"
    # os.mkdir(result_folder_path)

    # Download the YouTube video using the yt_dl module.
    # yt_download(URL, result_folder_path)

    # model = whisper.load_model("medium")
    # result = model.transcribe(f"{result_folder_path}/target.mp4")

    # # // save result as json
    # with open(f"{result_folder_path}/result.json", mode="w") as f:
    #     json.dump(result, f)

    
    # load result from json
    # with open(f"{result_folder_path}/result.json", mode="r") as f:
    #     result = json.load(f)


    # # Save the transcription as a text file.
    # with open(f"{result_folder_path}/transcript.txt", mode = "w") as f:
    #     f.write(result["text"])

    # # Generate subtitles.
    # # generate_subtitles(result, result_folder_path, translated_lang)
    
    app.launch()
    # Use the ffmpeg command to add the SRT subtitles to the video.
    # embed_subtitles(result_folder_path)

if __name__ == "__main__":
    main()
    