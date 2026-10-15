import config
from tkinter import *
import cv2
from PIL import Image, ImageTk
import threading
import pyaudio
from vosk import Model, KaldiRecognizer
import json
import queue
from deepface import DeepFace
import time


client = config.openai_client()

# Define global variables for thread control
playing = False

app = Tk()
app.title("Audiovisual Recorder")

# Frame for video display and buttons
main_frame = Frame(app)
main_frame.pack(side='top', fill=BOTH, expand=True)

# Frame for question bank management
question_frame = Frame(app)
question_frame.pack(side='bottom', fill=BOTH, expand=True)

# Dropdown for selecting question categories
category_var = StringVar(app)
category_dropdown = OptionMenu(question_frame, category_var, 'HR', 'Technical', 'Behavioral')
category_dropdown.pack(side='left', padx=10, pady=10)

# Entry widget for adding new questions
question_entry = Entry(question_frame, width=50)
question_entry.pack(side='left', padx=10, pady=10)

app.geometry("1200x768")  # Set the size of the window

# Create a left sidebar for navigation buttons
left_sidebar = Frame(app, width=200, bg='black')
left_sidebar.pack(side='left', fill='y')

# Create buttons for the sidebar
scores_button = Button(left_sidebar, text="My Scores", bg='black', fg='white')
scores_button.pack(padx=10, pady=10, fill='x')

mock_interview_button = Button(left_sidebar, text="Mock Interview", bg='black', fg='white')
mock_interview_button.pack(padx=10, pady=10, fill='x')

# Create a top bar for category and search
top_bar = Frame(app, bg='lightgray')
top_bar.pack(side='top', fill='x')

# Add dropdown and search bar to the top bar
category_label = Label(top_bar, text="Category", bg='lightgray')
category_label.pack(side='left', padx=10)

# Assuming category_var and category_dropdown are defined as before
category_dropdown.pack(side='left', padx=10)

search_entry = Entry(top_bar)
search_entry.pack(side='left', padx=10, fill='x', expand=True)

search_button = Button(top_bar, text="Search")
search_button.pack(side='left', padx=10)

# Create a frame for the video feed and question list
center_frame = Frame(app, bg='white')
center_frame.pack(side='top', expand=True, fill='both')



# Create a listbox for questions
question_listbox = Listbox(center_frame)
question_listbox.pack(side='right', fill='y', padx=10)

# Add question to the listbox (Placeholder for actual functionality)
question_listbox.insert('end', "Tell me about yourself")

# Create a bottom bar for control buttons
bottom_bar = Frame(app, bg='lightgray')
bottom_bar.pack(side='bottom', fill='x')


# Create a button to add new question to the listbox (Placeholder for actual functionality)
add_question_button = Button(bottom_bar, text="Add Question")
add_question_button.pack(side='right', padx=10, pady=10)

# Initialize video and audio systems
vid = cv2.VideoCapture(config.camera_index())
# Adjust the capture resolution
vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

sample_format = pyaudio.paInt16
channels = 1
fs = 16000  # Record at 16000 samples per second
chunk = 1024  # Record in chunks of 1024 samples
recognizer = KaldiRecognizer(Model(str(config.vosk_model_path())), fs)

video_queue = queue.Queue()
audio_queue = queue.Queue()
answer = ""

prev_frame_time = time.time()

def update_video(spf = 2):
    global prev_frame_time
    ret, frame = vid.read()
    if not ret:
        print("Error: Can't receive frame (stream end?). Exiting ...")
        return

    # Update the GUI with the frame regardless of the processing rate
    cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    pil_image = Image.fromarray(cv_image)
    image = ImageTk.PhotoImage(pil_image)
    video_label.config(image=image)
    video_label.image = image  # Keep a reference!
    if playing:

        # Check if it's time to process the frame
        curr_frame_time = time.time()
        if (curr_frame_time - prev_frame_time) > spf:  # Process one frame per second as per fps
            video_queue.put(frame)
            print(f"Video Queue Size: {video_queue.qsize()}")
            prev_frame_time = curr_frame_time

        # Schedule the next update
        app.after(10, update_video)
    else:
        vid.release()
        cv2.destroyAllWindows()


def capture_audio():
    p = pyaudio.PyAudio()  # Create an interface to PortAudio
    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)
    
    print("Recording audio started")
    while playing:
        data = stream.read(chunk)
        audio_queue.put(data)
    
    # Stop and close the stream 
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()
    print("Recording audio stopped")

def process_frame():
    while playing:
        if not video_queue.empty():
            frame = video_queue.get()
            try:
                # Convert the color space from BGR to RGB because DeepFace expects RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Analyze the image for emotions and get the first result since DeepFace.analyze returns a list
                analysis = DeepFace.analyze(frame_rgb, actions=['emotion'], enforce_detection=False)
                    
                # Extracting the dominant emotion
                dominant_emotion = analysis[0]['dominant_emotion']
                print(f"Dominant Emotion: {dominant_emotion}")
            except Exception as e:
                print(f"An error occurred: {e}")

def process_audio():
    global answer
    while playing or not audio_queue.empty():
        if not audio_queue.empty():
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                print(f"Recognized Text: {result.get('text', '')}")
                answer += result.get('text', '') + ' '


video_label = Label(main_frame)
video_label.pack(side=TOP, fill=BOTH, expand=True)

# Control buttons
start_button = Button(main_frame, text="Start Recording", command=lambda: start_recording())
start_button.pack(side='left', padx=10, pady=10)

stop_button = Button(main_frame, text="Stop Recording", command=lambda: stop_recording())
stop_button.pack(side='left', padx=10, pady=10)



app.bind('<Escape>', lambda e: stop_recording())


# Start and stop recording functions
def start_recording():
    global playing

    if not playing:
        playing = True
        update_video() 
        global audio_thread
        audio_thread = threading.Thread(target=capture_audio)
        audio_thread.start()
        analyse_video_thread = threading.Thread(target=process_frame, args=())
        analyse_video_thread.start()
        analyse_audio_thread = threading.Thread(target=process_audio, args=())
        analyse_audio_thread.start()

def stop_recording():
    global playing
    if playing:
        playing = False
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {
                "role": "system",
                "content": "You are a somewhat harsh interview grader. You will receive an input of a question the user has been asked, along with a transcript of their answer. Based on this, you will assign them a grade from A to F. Your output should be in the following format:\n\nGrade: C-\nExplanation: (3-5 sentences on why they received the grade they did, and give an example of a better response)"
                },
                {
                "role": "user",
                "content": f"Question: Tell me about yourself\nAnswer: {answer}"
                }
            ],
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        print(response.choices[0].message.content)


# Assuming video_label is defined as before to display video feed
video_label.pack(side='left', fill='both', expand=True)

app.mainloop()