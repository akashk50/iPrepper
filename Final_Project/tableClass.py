import config
import tkinter as tk
from tkinter import ttk

def fetch_dynamodb_data(table_name):
    # Setup AWS DynamoDB access
    dynamodb = config.dynamodb_resource()
    table = dynamodb.Table(table_name)
    response = table.scan()

    items = response.get('Items', [])
    while response.get('LastEvaluatedKey'):
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    return items

class Table:
    def __init__(self, root, items):
        # Predefined headers matching the DynamoDB table attributes
        headers = ['Select', 'dateSubmitted', 'Feedback', 'Question', 'Happy', 'Neutral', 'Other Emotions']  # example headers

        # Creating the treeview with predefined columns
        self.tree = ttk.Treeview(root, columns=headers, show='headings', height=(len(items)))
        self.tree.grid(row=20, column=0, sticky='nsew')
        
        # Setting up the columns
        self.tree.heading('Select', text='Select')
        self.tree.column('Select', width=50, anchor='center')
        for header in headers[1:]:  # Skip the 'Select' column for looping headers
            self.tree.heading(header, text=header)
            self.tree.column(header, width=250, anchor='w')

        # Data structure to keep track of checked items
        self.checked_items = {}

        # Inserting data into the treeview
        for item in items:
            values = ['☐']  # Start with an empty checkbox
            # Append other item values based on headers order, except 'Select'
            values += [item.get(header, '') for header in headers if header != 'Select']
            row_id = self.tree.insert('', 'end', values=values)
            self.checked_items[row_id] = False  # Initially, no item is checked

        # Binding the treeview selection
        self.tree.bind('<ButtonRelease-1>', self.check_item)

    def adjust_tree_height(self, change):
        current_height = int(self.tree.cget('height'))
        new_height = current_height + change
        self.tree.configure(height=new_height)

    def get_checked_items(self):
        return self.checked_items
    
    def delete_from_checked_items(self, key):
        del self.checked_items[key]

    def get_row_data(self, row_id):
        return self.tree.item(row_id)['values']
    
    def remove_row(self, row_id):
        self.tree.delete(row_id)
        self.adjust_tree_height(-1)

    def populate_table(self, items):
        self.tree.delete(*self.tree.get_children())  # Clear the tree
        self.checked_items.clear()
        for item in items:
            values = ['☐'] + [item.get(header) for header in self.tree["columns"] if header != 'Select']
            row_id= self.tree.insert('', 'end', values=values)
            self.checked_items[row_id] = False
    
    def add_row(self, new_item):
        headers = ['dateSubmitted', 'Feedback', 'Question', 'Happy', 'Neutral', 'Other Emotions']  # example headers
        # Start with an unchecked checkbox
        values = ['☐']
        # Append other item values based on headers order, derived from the new item dictionary
        # Use the class-defined headers to ensure consistency
        values += [new_item.get(header, '') for header in headers]  # Skip 'Select' as it is manually set
        # Insert the new item into the Treeview and save the row_id
        row_id = self.tree.insert('', 'end', values=values)
        self.checked_items[row_id] = False
        self.adjust_tree_height(1)
        # Initialize the checkbox state as unchecked
    def edit_row(self, row_id, new_data):
        headers = ['dateSubmitted', 'Feedback', 'Question', 'Happy', 'Neutral', 'Other Emotions']  # example headers
        # Update the values in the row identified by row_id with new_data
        values = ['☐'] + [new_data.get(header, '') for header in headers if header != 'Select']
        self.tree.item(row_id, values=values)



    def check_item(self, event):
        region = self.tree.identify('region', event.x, event.y)
        if region == 'cell':
            row_id = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            if column == '#1':  # Check if the checkbox column is clicked
                self.checked_items[row_id] = not self.checked_items[row_id]
                print(self.checked_items)
                self.update_checkbox(row_id)

    def update_checkbox(self, row_id):
        checked = '☑' if self.checked_items[row_id] else '☐'
        self.tree.set(row_id, 'Select', checked)


def delete_entries(t, table):
    #  listOfDeleted = [key for key,val in t.get_checked_items if val==True]
    checked = t.get_checked_items()
    checkedList = [key for key, value in checked.items() if value==True]
    for row in checkedList:    
        toDelete = str(t.get_row_data(row)[1])
        print(toDelete)
        response = table.delete_item(
        Key={
        'dateSubmitted': toDelete  # Replace 'dateSubmitted' with your table's actual primary key attribute name if different
        }
        )
        t.delete_from_checked_items(row)
        t.remove_row(row)


def filter_by_question(t, search):
    keyword = search
    all_items = fetch_dynamodb_data(config.DYNAMODB_TABLE)  # Fetch items (either cached or anew)
    filtered_items = [item for item in all_items if keyword.lower() in item['Question'].lower()]
    t.populate_table(filtered_items)

# Function to add a new entry
def add_entry(t, table):
    # Define a new window for adding an entry
    add_window = tk.Toplevel()
    add_window.title("Add Entry")

    # Define input fields for new data
    tk.Label(add_window, text="dateSubmitted").grid(row=0, column=0)
    date_submitted_entry = tk.Entry(add_window)
    date_submitted_entry.grid(row=0, column=1)

    tk.Label(add_window, text="Feedback").grid(row=1, column=0)
    feedback_entry = tk.Entry(add_window)
    feedback_entry.grid(row=1, column=1)

    tk.Label(add_window, text="Question").grid(row=2, column=0)
    question_entry = tk.Entry(add_window)
    question_entry.grid(row=2, column=1)

    tk.Label(add_window, text="Happy").grid(row=3, column=0)
    happy_entry = tk.Entry(add_window)
    happy_entry.grid(row=3, column=1)

    tk.Label(add_window, text="Neutral").grid(row=4, column=0)
    neutral_entry = tk.Entry(add_window)
    neutral_entry.grid(row=4, column=1)

    tk.Label(add_window, text="Other Emotions").grid(row=5, column=0)
    otherEmotions_entry = tk.Entry(add_window)
    otherEmotions_entry.grid(row=5, column=1)

    # Button to submit the new entry
    submit_button = tk.Button(add_window, text="Add", command=lambda: submit_new_entry(row_id="N/A", isEdit=False, 
        date_submitted=date_submitted_entry.get(), feedback=feedback_entry.get(), happy=happy_entry.get(), neutral=neutral_entry.get(), otherEmotions=otherEmotions_entry.get(),question=question_entry.get(), table=table, t=t))
    submit_button.grid(row=6, column=1)


def submit_new_entry(row_id, isEdit, date_submitted, feedback, question, happy, neutral, otherEmotions, table, t):

    # Add a new entry to the DynamoDB table
    new_item = {
        "dateSubmitted": date_submitted,
        "Feedback": feedback,
        "Question": question,
        "Happy": happy,
        "Neutral": neutral,
        "Other Emotions": otherEmotions
    }
    if not isEdit:
        table.put_item(Item=new_item)  # Add the new entry to the DynamoDB table
        print("success!")
        t.add_row(new_item)
    else:
        table.put_item(Item=new_item)
        t.edit_row(row_id=row_id, new_data=new_item)

def edit_entry(t, table):
    checked = t.get_checked_items()
    checkedList = [key for key, value in checked.items() if value==True]
    toEdit = t.get_row_data(checkedList[0])

    add_window = tk.Toplevel()
    add_window.title("Edit Entry")
    # Define input fields for new data
    tk.Label(add_window, text="dateSubmitted").grid(row=0, column=0)
    date_submitted_entry = tk.Label(add_window, text=toEdit[1], font=("Helvetica 9 italic", 12))
    date_submitted_entry.grid(row=0, column=1)

    tk.Label(add_window, text="Feedback").grid(row=1, column=0)
    feedback_entry = tk.Entry(add_window)
    feedback_entry.insert(0, toEdit[2]) 
    feedback_entry.grid(row=1, column=1)

    tk.Label(add_window, text="Question").grid(row=2, column=0)
    question_entry = tk.Entry(add_window)
    question_entry.insert(0, toEdit[3]) 
    question_entry.grid(row=2, column=1)

    tk.Label(add_window, text="Happy").grid(row=3, column=0)
    happy_entry = tk.Entry(add_window)
    happy_entry.insert(0, toEdit[4]) 
    happy_entry.grid(row=3, column=1)

    tk.Label(add_window, text="Neutral").grid(row=4, column=0)
    neutral_entry = tk.Entry(add_window)
    neutral_entry.insert(0, toEdit[5]) 
    neutral_entry.grid(row=4, column=1)

    tk.Label(add_window, text="Other Emotions").grid(row=5, column=0)
    otherEmotions_entry = tk.Entry(add_window)
    otherEmotions_entry.insert(0, toEdit[6]) 
    otherEmotions_entry.grid(row=5, column=1)

    # Button to submit the new entry
    submit_button = tk.Button(add_window, text="Edit", command=lambda: submit_new_entry(row_id=checkedList[0], isEdit=True,
        date_submitted=toEdit[1], feedback=feedback_entry.get(), happy=happy_entry.get(), neutral=neutral_entry.get(), otherEmotions=otherEmotions_entry.get(),question=question_entry.get(), table=table, t=t))
    submit_button.grid(row=6, column=1)



if __name__ == "__main__":
    root = tk.Tk()
    root.configure(background='white')
    root.title("Table with Checkboxes from DynamoDB")
    dynamodb = config.dynamodb_resource()
    table = dynamodb.Table(config.DYNAMODB_TABLE)

    # Fetch data from DynamoDB
    items = fetch_dynamodb_data(config.DYNAMODB_TABLE)

    # Create the table with fetched data
    t = Table(root, items)
    buttons = tk.Frame(root, bg='white')
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('Treeview', font=('Quicksand', 11), rowheight=75)
    style.configure('Treeview.Heading', font=('Quicksand', 14))

    style.configure('MenuButton.TButton', background = '#2f3d44', foreground = '#C8C8C9', width = 20, 
                borderwidth=0, focusthickness=3, focuscolor='#2f3d44', font=('Quicksand', 14, 'normal'))
    style.map('MenuButton.TButton', foreground=[('active','white')], background=[('active','#2f3d44')])

    pad = 50
    buttons.grid(row=0, column=0, pady=30)
    deleteEntriesButton = ttk.Button(buttons, text="Delete", style='MenuButton.TButton', command=lambda: delete_entries(t, table))
    deleteEntriesButton.grid(row=0, column=0, padx=pad)

    addEntriesButton = ttk.Button(buttons, text="Add", style='MenuButton.TButton', command=lambda: add_entry(t, table))
    addEntriesButton.grid(row=0, column=1, padx=pad)

    editEntriesButton = ttk.Button(buttons, text="Edit", style='MenuButton.TButton', command=lambda: edit_entry(t, table))
    editEntriesButton.grid(row=0, column=2, padx=pad)

    searchBar = tk.Entry(buttons, font=('Quicksand', 17))
    searchBar.grid(row=0, column=3, padx=(pad, 0))

    filterEntriesButton = ttk.Button(buttons, text="Filter", style='MenuButton.TButton', command=lambda: filter_by_question(t, searchBar.get()))
    filterEntriesButton.grid(row=0, column=4)
    root.mainloop()