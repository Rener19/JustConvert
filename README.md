# JustConvert 

**JustConvert** is a simple, lightweight, and user-friendly YouTube video and playlist downloader with a built-in converter. It allows you to easily grab your favorite content in either high-quality video (MP4) or audio-only (MP3) formats.

[Download it here](JustConvert.exe)
 
> This is my **very first personal project**! I built this as my project for my [Harvard CS50P Final Project](https://certificates.cs50.io/7b1610ec-ad37-46dd-9ce8-952b51d46de0.pdf?size=letter)

---

## ✨ Features

- **Video & Playlist Support:** Download individual videos or entire YouTube playlists.
- **MP4 & MP3 Formats:** Choose the specific available quality and format of your audio and video files
- **Asynchronous Downloads:** A multi-threaded architecture ensures the GUI stays responsive during the download process.
- **Clean UI:** Simple, no-nonsense interface built with Tkinter.

---

## 🛠️ Built With

- **[Python](https://www.python.org/):** The core programming language.
- **[Tkinter](https://docs.python.org/3/library/tkinter.html):** Used for the graphical user interface.
- **[Pytubefix](https://github.com/JuanBindez/pytubefix):** A library used to interact with YouTube's API and handle downloads.
- **[FFmpeg](https://ffmpeg.org/):** The engine used for merging and converting media streams.
- **[PyInstaller](https://pyinstaller.org/):** Used to bundle the script into a standalone Windows executable.

---

## 📖 How to Use

1. **Enter URL:** Paste the YouTube video or playlist link into the text box.
2. **Choose Format:** Select either **mp4** or **mp3** at the top.
3. **Select Quality:** Choose your preferred resolution or bitrate from the dropdown menus that appear. (Note: When downloading a playlist the highest quality available is automatically used)
4. **Download:** Click the "Download" button and select your destination folder.
5. **Wait:** The progress bar will keep you updated. Once finished, you'll receive a confirmation message!

---

## 📜 License

This project was created for educational purposes. Please use it responsibly and respect YouTube's Terms of Service.
