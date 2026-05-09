import os, sys
import threading
import subprocess
import tempfile
from subprocess import CREATE_NO_WINDOW
from pytubefix import YouTube
from pytubefix.contrib.playlist import Playlist
from pytubefix.cli import on_progress
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk


window = None
is_processing = False
app_closed = False
download_thread = None
is_downloading = False
stop_download = False


def is_playlist(url):  # check if yt link is playlist (refactored but same logic)
    return "playlist?" in url


def sanitize_title(title):
    return "".join(c for c in title if c.isalnum() or c in " -_").rstrip()


def get_extension(file_type):
    if file_type == 0:
        return ".mp4"
    elif file_type == 1:
        return ".mp3"
    else:
        raise ValueError("Invalid file type")


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    global window
    window = Tk()

    window.geometry("400x250")
    window.title("JustConvert")
    window.resizable(False, False)

    icon = PhotoImage(file=resource_path("JustConvert.png"))

    window.iconphoto(True, icon)

    # label
    urlLabel = Label(window, text="Enter video/playlist URL: ")
    urlLabel.pack()
    urlLabel.place(x=10, y=5)

    # urlentrybox
    global urlbox
    urlbox = Entry()
    urlbox.pack()
    urlbox.config(width=48)
    urlbox.place(x=10, y=25)

    def enter():
        global is_processing, running
        if app_closed:
            return
        if is_processing:  # already working on a link
            messagebox.showinfo(
                title="TEKA LANG",
                message="A video/playlist is currently in process, click RESET first",
            )
            print("Already processing a download, please wait...")
            return
        is_processing = True

        url = urlbox.get()
        try:
            process_link(url, fileType.get())
        except Exception as e:
            urlbox.delete(0, END)
            urlbox.insert(0, "Invalid URL")
            is_processing = False
            print(e)

    # EnterButton
    enterButton = Button(window, text="Enter", command=enter)
    enterButton.pack()
    enterButton.config(width=10)
    enterButton.place(x=310, y=23)

    # mp3/mp4 rad button
    radChoices = ["mp4", "mp3"]

    fileType = IntVar()
    for i in range(len(radChoices)):
        mp3ormp4 = Radiobutton(
            window,
            text=radChoices[i],
            variable=fileType,  # groups radbuttons together with same variable
            value=i,
        )
        mp3ormp4.pack()
        mp3ormp4.place(x=150 + (i * 50), y=0)

    # gawa ng dropdown menu for mp4 and mp3 chjoices
    global mp4_options
    mp4_options = {}
    global mp3_options
    mp3_options = {}

    resetButton = Button(window, text="Reset", command=reset_ui)
    resetButton.pack()
    resetButton.config(width=10)
    resetButton.place(x=310, y=55)

    def on_closing():
        global app_closed, is_downloading
        app_closed = True
        if is_downloading:
            answer = messagebox.askyesno(
                "Confirm Exit",
                "A download is still in progress.\nAre you sure you want to close the app?",
            )
            if answer:
                print("Window closed, stopping program...")
                window.quit()  # Stops the Tkinter main loop
                window.destroy()
                sys.exit()
            else:
                return  # do nothing (stay open)
        else:
            print("Window closed, stopping program...")
            window.quit()  # Stops the Tkinter main loop
            window.destroy()
            sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_closing)

    window.mainloop()  # open window and listen for events


def reset_ui():
    global is_processing, is_downloading, vidtag, audtag
    if is_downloading:  # already working on a link
        messagebox.showinfo(
            title="TEKA LANG",
            message="A video/playlist is currently downloading, please wait for it to finish",
        )
        print("Already processing a download, please wait...")
        return
    # Destroy dropdowns and download button
    destroy_widgets()

    # Clear the URL box
    urlbox.delete(0, END)

    # Reset processing state
    is_processing = False

    # Reset selected tags
    vidtag = None
    audtag = None


# END OF TKINTER WINDOW CODE
###########################################################
def process_link(url, fileType):
    if is_playlist(url):
        pl = Playlist(url)
        for pl_url in pl.video_urls:
            print(pl_url)
        destroy_widgets()
        title = pl.title
        if len(title) > 20:
            title = title[:40] + "..."
        global titleLabel,plDownloadCount
        titleLabel = Label(window, text=f"Playlist Name: {title}")
        titleLabel.pack()
        titleLabel.place(x=10, y=50)
        plDownloadCount = Label(window)
        plDownloadCount.place(x=10, y=70)
        def finish_selection():
            global app_closed, is_downloading
            if is_downloading:
                messagebox.showinfo(
                    title="ISA ISA LANG", message="wait lang po may nagdodownload pa"
                )
                return

            if app_closed:
                return
            global progress_bar, progress_label, progress_status
            progress_status = Label(window, text="Starting download...")
            progress_bar = ttk.Progressbar(
                window, orient="horizontal", length=350, mode="determinate"
            )
            progress_label = Label(window, text="Progress: 0%")
            is_downloading = True
            download_playlist_files(pl, fileType)
            is_downloading = False

        global dlButton
        dlButton = Button(
            window, text="Download", command=finish_selection, compound=CENTER
        )
        dlButton.place(x=165, y=120)

    else:
        yt = YouTube(
            url, on_progress_callback=on_progress, on_complete_callback=on_complete
        )
        print(yt.title)
        print(yt.thumbnail_url)

        display_streams(yt, fileType)


mp4_menu = None
mp3_menu = None
dlButton = None
titleLabel = None
plDownloadCount = None
plDownloadCounter = 0
progress_bar = None
progress_label = None
progress_status = None


def destroy_widgets():
    for widget in (
        mp4_menu,
        mp3_menu,
        dlButton,
        titleLabel,
        plDownloadCount,
        progress_label,
        progress_bar,
        progress_status,
    ):
        try:
            widget.destroy()
        except Exception as e:
            print(widget, e)
            pass


def display_streams(obj, fileType):
    global mp4_menu, mp3_menu, dlButton, titleLabel  # keep references so we can destroy them
    global is_downloading, download_thread
    # Destroy old widgets if they exist
    destroy_widgets()

    def set_vidtag(choice):
        global vidtag
        vidtag = int(mp4_options[choice])
        print(vidtag)

    def set_audtag(choice):
        global audtag
        audtag = int(mp3_options[choice])
        print(audtag)

    def finish_selection():

        global app_closed, is_downloading, download_thread
        if is_downloading:
            messagebox.showinfo(
                title="ISA ISA LANG", message="wait lang po may nagdodownload pa"
            )
            return

        if app_closed:
            return

        def download_na():
            global is_downloading, stop_download
            is_downloading = True
            stop_download = False
            try:
                global progress_bar, progress_label, progress_status
                progress_status = Label(window, text="Starting download...")
                progress_bar = ttk.Progressbar(
                    window, orient="horizontal", length=350, mode="determinate"
                )
                progress_label = Label(window, text="Progress: 0%")
                if fileType == 0:
                    directory = ask_output_directory(obj.title)
                    if directory:
                        download_file(obj, vidtag, audtag, directory)
                        if window.winfo_exists():
                            messagebox.showinfo(title="CONGRATS", message="download has been finished")

                else:
                    directory = ask_output_directory(obj.title, extension=".mp3")
                    if directory:
                        download_file(obj, 0, audtag, directory)
                        if window.winfo_exists():
                            messagebox.showinfo(title="CONGRATS", message="download has been finished")

            except Exception as e:
                print(e)
            finally:
                is_downloading = False
                reset_ui()

        download_thread = threading.Thread(target=download_na, daemon=True)
        download_thread.start()
        is_downloading = True

    # show ang drop menu sa window

    mp4_options.clear()
    mp3_options.clear()

    title = obj.title
    if len(title) > 50:
        title = title[:50] + "..."

    titleLabel = Label(window, text=title)
    titleLabel.pack()
    titleLabel.place(x=10, y=50)

    # This part kukunin at isasave ung mga options ng mp4 and mp3
    if fileType == 0:
        for stream in obj.streams.filter(only_video=True):
            res = f"{stream.resolution} {stream.video_codec}"
            vtag = stream.itag
            mp4_options[res] = vtag

        for stream in obj.streams.filter(only_audio=True):
            bitr = f"{stream.abr}  {stream.audio_codec}"
            atag = stream.itag
            mp3_options[bitr] = atag

        chosenvidtag = StringVar()
        firstvidtag = next(iter(mp4_options.keys()))
        chosenvidtag.set(firstvidtag)
        set_vidtag(firstvidtag)
        mp4_menu = OptionMenu(
            window, chosenvidtag, *mp4_options.keys(), command=set_vidtag
        )
        mp4_menu.config(width=20)
        mp4_menu.pack()
        mp4_menu.place(x=30, y=90)

        chosenaudtag = StringVar()
        firstaudtag = next(iter(mp3_options.keys()))
        chosenaudtag.set(firstaudtag)
        set_audtag(firstaudtag)
        mp3_menu = OptionMenu(
            window, chosenaudtag, *mp3_options.keys(), command=set_audtag
        )
        mp3_menu.config(width=20)
        mp3_menu.pack()
        mp3_menu.place(x=200, y=90)

    elif fileType == 1:
        for stream in obj.streams.filter(only_audio=True):
            bitr = f"{stream.abr}  {stream.audio_codec}"
            atag = stream.itag
            mp3_options[bitr] = atag

        chosenaudtag = StringVar()
        firstaudtag = next(iter(mp3_options.keys()))
        chosenaudtag.set(firstaudtag)
        set_audtag(firstaudtag)
        mp3_menu = OptionMenu(
            window, chosenaudtag, *mp3_options.keys(), command=set_audtag
        )
        mp3_menu.config(width=20, compound=CENTER)
        mp3_menu.pack()
        mp3_menu.place(x=115, y=80)

    dlButton = Button(
        window, text="Download", command=finish_selection, compound=CENTER
    )
    dlButton.pack()
    dlButton.place(x=165, y=120)


def on_progress(stream, chunk, bytes_remaining):  # for loading bar on progress
    global progress_bar, progress_label
    if progress_bar is None or progress_label is None:
        return  # do nothing if not created

    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent = int(bytes_downloaded / total_size * 100)

    # update safely in GUI thread
    window.after(0, lambda: update_progress(percent))


def update_progress(percent):
    global progress_bar, progress_label, progress_status
    if progress_bar and progress_label:
        try:
            progress_bar["value"] = percent
            progress_label.config(text=f"Progress: {percent}%")
            progress_bar.update_idletasks()
        except TclError:
            # If user closed the window while downloading
            pass


def on_complete(stream, file_path):  # when loading bar is completed
    global progress_bar, progress_label
    if progress_bar and progress_label:
        try:
            window.after(0, lambda: update_progress(100))
            window.after(0, lambda: progress_label.config(text="Download complete ✅"))
            window.after(0, lambda: progress_status.config(text="Download complete ✅"))
        except TclError:
            # widget was destroyed before update
            pass


def is_playlist(url):  # check if yt link is playlist
    if "playlist?" in url:
        return True
    return False


def ask_output_directory(title, extension=".mp4"):
    # Open file dialog to choose output path

    safe_title = sanitize_title(title)


    ext = extension

    if ext == ".mp4":
        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4")],
            title="Save Final Output As",
            initialfile=f"{safe_title}.mp4",
        )
    else:
        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3")],
            title="Save Final Output As",
            initialfile=f"{safe_title}.mp3",
        )

    if not output_path:
        print("No file selected. Cancelling...")
        return
        # Delete file if it already exists
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"Deleted existing file: {output_path}")
        except PermissionError:
            print(f"Cannot delete existing file (permission denied): {output_path}")
            return None

    return output_path


def download_file(
    yt_obj, vidstream, audstream, output_path, from_playlist=False
):  # download vid in given link

    global is_downloading, progress_label, progress_bar, progress_status
    try:
        if not from_playlist:
            progress_status.place(x=20, y=150)

            progress_bar.pack(pady=10)
            progress_bar.place(x=20, y=170)

            progress_label.place(x=20, y=200)

        if vidstream != 0:
            video_stream = yt_obj.streams.get_by_itag(vidstream)
            progress_bar["value"] = 0
            window.after(
                0,
                lambda: progress_status.config(
                    text=f"Downloading Video of {yt_obj.title[:30]}..."
                ),
            )
            video_path = video_stream.download(output_path=tempfile.gettempdir(), filename="video.mp4")

            audio_stream = yt_obj.streams.get_by_itag(audstream)
            progress_bar["value"] = 0
            window.after(
                0,
                lambda: progress_status.config(
                    text=f"Downloading Audio of {yt_obj.title[:30]}..."
                ),
            )
            audio_path = audio_stream.download(output_path=tempfile.gettempdir(), filename="audio.mp3")

            progress_label.config(
                text=f"Combining Video and Audio file of {yt_obj.title[:15]}... pls wait..."
            )

            ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")

            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    print(f"Deleted existing file: {output_path}")
                except PermissionError:
                    print(
                        f"Cannot delete existing file (permission denied): {output_path}"
                    )
                    return None

            command = [
                ffmpeg_path,
                "-i",
                video_path,
                "-i",
                audio_path,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-strict",
                "experimental",
                output_path,
            ]
            subprocess.run(command, creationflags=CREATE_NO_WINDOW)

            # Optional: Clean up intermediate files
            os.remove(video_path)
            os.remove(audio_path)
        else:
            audio_stream = yt_obj.streams.get_by_itag(audstream)
            progress_bar["value"] = 0
            window.after(
                0,
                lambda: progress_status.config(
                    text=f"Downloading Audio of {yt_obj.title[:30]}..."
                ),
            )
            # Split full path into folder and filename
            folder = os.path.dirname(output_path)
            filename = os.path.basename(output_path)

            # Download the audio stream
            audio_stream.download(output_path=folder, filename=filename)
    except Exception as e:
        print(e)


def download_playlist_files(playlist, extension):
    global progress_bar, progress_label, is_downloading, progress_status, plDownloadCount

    def download_na():
        global is_downloading
        is_downloading = True
        try:

            folder = filedialog.askdirectory(title="Select Output Folder")
            if not folder:
                print("No folder selected. Cancelling...")
                return None

            global plDownloadCount, plDownloadCounter

            progress_status.place(x=20, y=150)

            progress_bar.pack(pady=10)
            progress_bar.place(x=20, y=170)

            progress_label.place(x=20, y=200)

            # Create progress bar once
            progress_bar["value"] = 0
            progress_label.config(text="Progress: 0%")

            for url in playlist.video_urls:
                try:
                    pl_vid = YouTube(
                        url,
                        on_progress_callback=on_progress,
                        on_complete_callback=on_complete,
                    )
                    audio_stream = (
                        pl_vid.streams.filter(only_audio=True, mime_type="audio/mp4")
                        .order_by("abr")
                        .desc()
                    )

                    if extension == 0:
                        video_stream = pl_vid.streams.get_highest_resolution(
                            progressive=False
                        ).itag
                    else:
                        video_stream = 0

                except Exception as e:
                    print(f"Error getting streams for {url}: {e}")
                    continue

                file_title = pl_vid.title
                safe_title = sanitize_title(file_title)

                extensionname = get_extension(extension)

                filename = f"{safe_title}{extensionname}"
                directory = os.path.join(folder, filename)

                # Reset progress bar for each new file
                progress_bar["value"] = 0
                progress_label.config(text="Progress: 0% ")
                plDownloadCounter += 1
                window.after(
                    0,
                    lambda t=file_title: progress_status.config(
                        text=f"Downloading {t[:30]}"
                    ),
                )
                window.after(0, lambda count = f"{plDownloadCounter}/{len(playlist.video_urls)}": plDownloadCount.config(text=f"Downloading files {count}"))

                # Set downloading flag
                is_downloading = True
                download_file(
                    pl_vid,
                    video_stream,
                    audio_stream.first().itag,
                    directory,
                    from_playlist=True,
                )

            if window.winfo_exists():
                messagebox.showinfo(title="CONGRATS", message="download has been finished")
        except Exception as e:
            print(e)
        finally:
            is_downloading = False
            plDownloadCounter = 0
            reset_ui()

    download_thread = threading.Thread(target=download_na, daemon=True)
    download_thread.start()
    is_downloading = True


if __name__ == "__main__":
    main()
