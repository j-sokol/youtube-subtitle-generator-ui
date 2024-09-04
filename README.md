# YouTube Subtitle Generator WebUI


## Description

WebUI to generate subtitles for YouTube videos with translation to various languages



## Setup
Install this repository with the following command:

    git clone https://github.com/j-sokol/youtube-subtitle-generator-ui

In order to execute this code, the required modules must be installed:

    pip install -r requirements.txt

It also requires the command-line tool [`ffmpeg`](https://ffmpeg.org/) to be installed on your system, which is available from most package managers:

```bash
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```

## Usage
Execute main.py with the following command.

    python3 main.py

