import config
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
from tkinter import font
import customtkinter
from pymongo import MongoClient
import time
import queue
import threading
from threading import Thread
import pyaudio
from vosk import Model, KaldiRecognizer
import json
from deepface import DeepFace
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.font_manager import FontProperties
from functools import reduce
from datetime import datetime
from decimal import Decimal
import tableClass as tab


app = tk.Tk()
app.title("iPrepper")
app.geometry('1600x900')

# Credentials are read only when the application is launched.
openAIClient = config.openai_client()
dynamodb = config.dynamodb_resource()
dynamoTable = dynamodb.Table(config.DYNAMODB_TABLE)

menu_frame = tk.Frame(app, bg='#2f3d44')
main_frame = tk.Frame(app, bg='white')
header_frame = tk.Frame(app, bg='#2f3d44')
analytics_frame = tk.Frame(app, bg='white')

menu_frame.place(x=0, y=0, height=900, width=500)
main_frame.place(x=500, y=90, height=810, width=1100)
header_frame.place(x=500, y=0, width=1100, height=90)
analytics_frame.place(x=0, y=90, width=1600, height=830)

search_var = tk.StringVar()

style = ttk.Style(app)
style.theme_use('clam')  # Using a theme that allows for customization

#variable definitions
playing = False
prev_frame_time = time.time()
video_queue = queue.Queue()
audio_queue = queue.Queue()
answer = ""
emotionsDict = {}




def raiseFrame(*frames):
    for frame in frames:
        frame.tkraise()

style.configure('MenuButton.TButton', background = '#2f3d44', foreground = '#C8C8C9', width = 20, 
                borderwidth=0, focusthickness=3, focuscolor='#2f3d44', font=('Quicksand', 14, 'normal'))
style.map('MenuButton.TButton', foreground=[('active','white')], background=[('active','#2f3d44')])


items = tab.fetch_dynamodb_data(config.DYNAMODB_TABLE)

    # Create the table with fetched data
t = tab.Table(analytics_frame, items)
# header buttons
analytics_header = ttk.Button(header_frame, style='MenuButton.TButton', command=lambda: raiseFrame(analytics_frame), text="Analytics")
analytics_header.place(x=800, y=20, width=75, height=40)

interview_prep_header = ttk.Button(header_frame, style = 'MenuButton.TButton', command=lambda: raiseFrame(main_frame, menu_frame), text="Prep Tool")
interview_prep_header.place(x=900, y=20, width=77, height=40)


table = dynamoTable

# Create the table with fetched data
buttons = tk.Frame(analytics_frame, background='white')
style = ttk.Style(analytics_frame)
style.theme_use('clam')
style.configure('Treeview', font=('Quicksand', 11), rowheight=75)
style.configure('Treeview.Heading', font=('Quicksand', 14))

style.configure('MenuButton.TButton', background = '#2f3d44', foreground = '#C8C8C9', width = 20, 
            borderwidth=0, focusthickness=3, focuscolor='#2f3d44', font=('Quicksand', 14, 'normal'))
style.map('MenuButton.TButton', foreground=[('active','white')], background=[('active','#2f3d44')])

pad = 50
buttons.grid(row=0, column=0, pady=30)
deleteEntriesButton = ttk.Button(buttons, text="Delete", style='MenuButton.TButton', command=lambda: tab.delete_entries(t, table))
deleteEntriesButton.grid(row=0, column=0, padx=pad)

addEntriesButton = ttk.Button(buttons, text="Add", style='MenuButton.TButton', command=lambda: tab.add_entry(t, table))
addEntriesButton.grid(row=0, column=1, padx=pad)

editEntriesButton = ttk.Button(buttons, text="Edit", style='MenuButton.TButton', command=lambda: tab.edit_entry(t, table))
editEntriesButton.grid(row=0, column=2, padx=pad)

searchBar = tk.Entry(buttons, font=('Quicksand', 17))
searchBar.grid(row=0, column=3, padx=(pad, 0))

filterEntriesButton = ttk.Button(buttons, text="Filter", style='MenuButton.TButton', command=lambda: tab.filter_by_question(t, searchBar.get()))
filterEntriesButton.grid(row=0, column=4)


# Function to update the video feed
def update_video_label(spf=1):
    global prev_frame_time
    ret, frame = cap.read()
    if not ret:
        print("error")
    else:
        # Convert the image from BGR (OpenCV format) to RGB (Tkinter format)
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgresized = img.resize((960, 540), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=imgresized)
        
        # Update the label with the new image
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)
        
        if playing:
            curr_frame_time = time.time()
            if (curr_frame_time - prev_frame_time) > spf:  # Process one frame per second as per fps
                video_queue.put(frame)
                print(f"Video Queue Size: {video_queue.qsize()}")
                prev_frame_time = curr_frame_time

        # Repeat after an interval to get the next frame
        video_label.after(40, update_video_label)


sample_format = pyaudio.paInt16
channels = 1
fs = 16000  # Record at 16000 samples per second
chunk = 1024  # Record in chunks of 1024 samples
recognizer = KaldiRecognizer(Model(str(config.vosk_model_path())), fs)

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
# Label for displaying the video

def process_audio():
    global answer
    while playing or not audio_queue.empty():
        if not audio_queue.empty():
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                answer += result.get('text', '') + ' '
    print("Answer: ", answer)

def process_frame():
    while not video_queue.empty():
        frame = video_queue.get()
        try:
            # Convert the color space from BGR to RGB because DeepFace expects RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Analyze the image for emotions and get the first result since DeepFace.analyze returns a list
            analysis = DeepFace.analyze(frame_rgb, actions=['emotion'], enforce_detection=False)
                
            # Extracting the dominant emotion
            dominant_emotion = analysis[0]['dominant_emotion']
            print(f"Dominant Emotion: {dominant_emotion}")
            emotionsDict[dominant_emotion] = emotionsDict.get(dominant_emotion, 0) + 1
        except Exception as e:
            print(f"An error occurred: {e}")


video_label = tk.Label(main_frame, borderwidth=0)
video_label.place(x=26,y=150)

feedback_frame = tk.Frame(main_frame, borderwidth=0, background='#2f3d44')
feedback_label = tk.Label(feedback_frame, text="feedbackText", background='#2f3d44', fg='#FFFFFF', anchor='nw', font=('Quicksand', 22, 'normal'))

def create_chart(feedback_frame):
    # Data for plotting
    font = FontProperties(family='sans-serif')
    values = []
    mylabels = []
    colors = colors = [
    '#FF6F61',  # Vibrant pink
    '#6B5B95',  # Amethyst purple
    '#88B04B',  # Pear green
    '#F7CAC9',  # Pale pink
    '#92A8D1',  # Soft blue
    '#955251',  # Chestnut brown
    '#B565A7',  # Raspberry pink
    '#009B77',  # Tropical green
    '#DD4124',  # Fiery orange
    '#D65076',  # Magenta pink
    ]
    for x, y in emotionsDict.items():
        mylabels.append(x)
        values.append(y)

    # Create a figure
    fig = Figure(figsize=(4, 4), dpi=100)
    fig.patch.set_facecolor('#2f3d44')  # Set the background of the figure to black
    plot = fig.add_subplot(111)  # Create a subplot
    plot.set_facecolor('#2f3d44')  # Set the Axes background color to black
    
    # Plot data
    wedges, texts, autotexts = plot.pie(values, labels=mylabels, autopct='%1.1f%%', colors=colors,
                                        textprops={'color':"white", 'fontproperties': font})
    
    # Customize the title and its color
    plot.set_title("Emotional Analysis", color='white')
    
    # Customize label colors
    for text in texts:
        text.set_color('white')
    
    # Creating a canvas to draw the pie chart onto and add to the Tkinter frame
    canvas = FigureCanvasTkAgg(fig, master=feedback_frame)
    canvas.draw()
    canvas.get_tk_widget().place(x=0,y=0)


textHeaderMain = text_label = tk.Label(main_frame, text="Interview Prep", bg='#FFFFFF', font=('Quicksand', 28, 'normal'), fg='#000000')
textHeaderMain.place(x=26, y=10)

textQuestionMain = text_label = tk.Label(main_frame, text="No question to display yet", bg='#FFFFFF', font=('Quicksand', 18, 'normal'), fg='#000000')
textQuestionMain.place(x=26, y=60)

results_listbox = tk.Listbox(menu_frame)


# OpenCV video capture
cap = cv2.VideoCapture(config.camera_index())  # Use 0 for the default camera

custom_font = font.Font(family='Quicksand', size=32, weight='normal')

logoimg = Image.open(config.asset_path('logo.ppm'))
resized = logoimg.resize((50, 50), Image.Resampling.LANCZOS)
tkimg = ImageTk.PhotoImage(resized)
label1 = tk.Label(menu_frame, image = tkimg, bg='#2f3d44')
label1.place(x=5,y=10, width=50, height=50)



tlogo = text_label = tk.Label(menu_frame, text="iPrepper", bg='#2f3d44', font=custom_font, fg='#ffffff')
tlogo.place(x=60, y=10)

textSearchQuestionHeader = text_label = tk.Label(menu_frame, text="Search for a Specific Question", bg='#2f3d44', font=('Quicksand', 15, 'bold'), fg='#ffffff')
textSearchQuestionHeader.place(x=18, y=100)

# Search entry
def on_focus_in(event):
    results_listbox.place_forget()
search_entry = tk.Entry(menu_frame, textvariable=search_var, highlightthickness=0, highlightbackground='#2f3d44',highlightcolor='#2f3d44', borderwidth=0)
search_entry.place(x=20, y=140, width=425, height=35)
search_entry.bind("<FocusIn>", on_focus_in)

textFilterQuestionHeader = text_label = tk.Label(menu_frame, text="Filter", bg='#2f3d44', font=('Quicksand', 15, 'bold'), fg='#ffffff')
textFilterQuestionHeader.place(x=18, y=195)

textDifficultyHeader = text_label = tk.Label(menu_frame, text="Difficulty", bg='#2f3d44', font=('Quicksand', 11, 'bold'), fg='#9aa1a8')
textDifficultyHeader.place(x=18, y=230)

sliderValue = 5

def getSliderValue(value):
    global sliderValue
    sliderValue = value

sliderDifficulty = customtkinter.CTkSlider(menu_frame, width=425, from_=1, to=10,fg_color='#2D853D', progress_color='#1ced13', number_of_steps=9, button_color='#1ced13', button_hover_color='#2D853D', command=getSliderValue)
sliderDifficulty.place(x=18, y=250)

textSliderStartHeader = text_label = tk.Label(menu_frame, text="1", bg='#2f3d44', font=('Quicksand', 14, 'normal'), fg='#FFFFFF')
textSliderStartHeader.place(x=19, y=270, height=13)

textSliderEndHeader = text_label = tk.Label(menu_frame, text="10", bg='#2f3d44', font=('Quicksand', 14, 'normal'), fg='#FFFFFF')
textSliderEndHeader.place(x=425, y=270, height=13)

# Remove border by setting the border width to 0
style.configure('TMenubutton', borderwidth=0)

# Change highlight color
style.map('TMenubutton', background='#FFFFFF')  # Change '#FFFFFF' to the desired color

# Now, use ttk.OptionMenu instead of tk.OptionMenu


style.configure('TButton', background = '#1ced13', foreground = 'white', width = 20, borderwidth=0, focusthickness=3, focuscolor='none', 
                font=('Quicksand', 14, 'normal'),
                )
style.map('TButton', background=[('active','#1ced13')])


def perform_search():
    search_query = search_var.get().lower()  # Get the current value from the search entry
    diffVal = int(sliderValue)  # Use the global sliderValue, ensure it's an integer
    print(diffVal)
    def query_db():
        regex_pattern = {'$regex': search_query, '$options': 'i'}
        client = MongoClient(config.MONGODB_URI)
        db = client[config.MONGODB_DATABASE]
        questions = db.questions
        try:
            documents = questions.find({"Question": regex_pattern, "Difficulty": diffVal})
            # Clear the listbox before inserting new items
            results_listbox.delete(0, tk.END)
            for doc in documents:
                results_listbox.insert(tk.END, doc['Question'])  # Use doc['Question'] instead of doc.Question
        finally:
            client.close()  # Ensure the connection is closed after the query

        results_listbox.place(x=20, y=175, width=425, height=60)
        results_listbox.tkraise()

    # Run the query in a separate thread to avoid blocking the main UI thread
    Thread(target=query_db).start()

question = "no question here..."
def update_label(event):
    global question
    # Get the index of the selected line
    index = results_listbox.curselection()
    if index:  # Check if there is a selection
        # Get the line's text
        selected_text = results_listbox.get(index)
        # Update the label's text
        question = selected_text
        textQuestionMain.config(text=selected_text)

results_listbox.bind("<<ListboxSelect>>", update_label)



# Search button
search_button = ttk.Button(menu_frame, cursor='man', text="Search", style='TButton', command=lambda: perform_search())
search_button.place(x=20, y=320, width=100, height=35)


# Play and stop buttons

def play_action(event):
    global playing
    if not playing:
        playing = True
        print(playing)
        global audio_thread
        audio_thread = threading.Thread(target=capture_audio)
        audio_thread.start()

def stop_action(event):
    global playing
    if playing:
        playing = False
        print(playing)
        analyse_audio_thread = threading.Thread(target=process_audio, args=())
        analyse_audio_thread.start()
        analyse_video_thread = threading.Thread(target=process_frame, args=())
        analyse_video_thread.start()
        analyse_video_thread.join()
        analyse_audio_thread.join()
        print(answer)
        totalEmotions = reduce(lambda x,y: x+y, emotionsDict.values())
        feedback_frame.place(x=26,y=150, width=960, height=540)
        create_chart(feedback_frame=feedback_frame)
        userContent = f"Question: {question}\nAnswer: {answer}"
        print(userContent)
        response = openAIClient.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                    "role": "system",
                    "content": "You are an interview prep helper. You will receive an input of a question the user has been asked, along with a transcript of their answer. Based on this, you will assign them a grade from A to F. This grade should have nothing to do with grammar, spacing, or run on sentences, and should be exclusively to do with actual content of the answer. Your output should be in the following format:\n\nGrade: C-\nExplanation: (3-5 sentences on why they received the grade they did, and constructive feedback to improve it)"
                    },
                    {
                    "role": "user",
                    "content": userContent
                    }
                ],
                temperature=1,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
        out = response.choices[0].message.content
        print(question)
        print(out)
        print(emotionsDict)
        print(totalEmotions)
        dynamoItem = {
            "dateSubmitted": str(datetime.now()), 
            "Question": question,
            "Feedback": out, 
            "Happy": Decimal(str(round(emotionsDict.get('happy', 0) / totalEmotions, 3))),
            "Neutral": Decimal(str(round(emotionsDict.get('neutral', 0) / totalEmotions, 3))),
            "Other Emotions": Decimal(str(round((totalEmotions - (emotionsDict.get('happy', 0) + emotionsDict.get('neutral', 0))) / totalEmotions, 3)))
        }
        dynamoTable.put_item(Item=dynamoItem)
        feedback_label.config(text=out, wraplength=380)
        t.adjust_tree_height(1)
        feedback_label.place(relx=0.55, y=10, relheight=1, relwidth=0.4)



playPauseFrame = tk.Frame(main_frame, bg='#2f3d44')
playPauseFrame.place(y=690, x=26, width=960, height=100)
# The original play/stop PNGs were not included; use text controls.
playButton = tk.Label(main_frame, text="▶", font=('Arial', 32), bg='#2f3d44', fg='white')
playButton.place(x=450, y=700)
playButton.bind("<Button-1>", play_action)

stopButton = tk.Label(main_frame, text='■', font=('Arial', 32), bg='#2f3d44', fg='white')
stopButton.place(x=550, y=700)
stopButton.bind("<Button-1>", stop_action)

update_video_label()

app.mainloop()
