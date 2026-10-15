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

#  initialization for 

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


dynamodb = config.dynamodb_resource()
table = dynamodb.Table(config.DYNAMODB_TABLE)

# Fetch data from DynamoDB
items = tab.fetch_dynamodb_data(config.DYNAMODB_TABLE)

# Create the table with fetched data
buttons = tk.Frame(analytics_frame)
style = ttk.Style(analytics_frame)
style.theme_use('clam')
style.configure('Treeview', font=('Quicksand', 11), rowheight=25)
style.configure('Treeview.Heading', font=('Quicksand', 14))

style.configure('MenuButton.TButton', background = '#2f3d44', foreground = '#C8C8C9', width = 20, 
            borderwidth=0, focusthickness=3, focuscolor='#2f3d44', font=('Quicksand', 14, 'normal'))
style.map('MenuButton.TButton', foreground=[('active','white')], background=[('active','#2f3d44')])

pad = 15
buttons.grid(row=0, column=0, pady=30)
deleteEntriesButton = ttk.Button(buttons, text="Delete", style='MenuButton.TButton', command=lambda: tab.delete_entries(t, table))
deleteEntriesButton.grid(row=0, column=0, padx=pad)

addEntriesButton = ttk.Button(buttons, text="Add", style='MenuButton.TButton', command=lambda: tab.add_entry(t, table))
addEntriesButton.grid(row=0, column=1, padx=pad)

editEntriesButton = ttk.Button(buttons, text="Edit", style='MenuButton.TButton', command=lambda: tab.edit_entry(t, table))
editEntriesButton.grid(row=0, column=2, padx=pad)

searchBar = tk.Entry(buttons)
searchBar.grid(row=0, column=3, padx=(pad, 0))

filterEntriesButton = ttk.Button(buttons, text="Filter", style='MenuButton.TButton', command=lambda: tab.filter_by_question(t, searchBar.get()))
filterEntriesButton.grid(row=0, column=4)

app.mainloop()