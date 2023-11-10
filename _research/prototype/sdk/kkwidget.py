import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
# 3rd party
import kkpyutil as util


class Page(ttk.LabelFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, text=title, **kwargs)
        self.grid_columnconfigure(0, weight=1)

    @staticmethod
    def add(widgets):
        for wgt in widgets:
            wgt.pack(fill="x", padx=5, pady=5, anchor="w")

    def get_title(self):
        return self.cget('text')

    def pack(self):
        super().pack(fill="x", pady=5)


class Entry(ttk.Frame):
    """
    - used as user input, similar to CLI arguments
    - widget must belong to a group
    - groups form a tree to avoid overloading parameter panes
    - groups also improves SNR by prioritizing frequently-tweaked parameters
    """

    def __init__(self, master: Page, text, widget_constructor, default, doc, **widget_kwargs):
        super().__init__(master)
        self.text = text
        self.default = default
        # model-binding
        self.data = None
        # label
        self.label = ttk.Label(self, text=self.text)
        self.label.grid(row=0, column=0, sticky='w')
        self.label.bind("<Double-Button-1>", lambda e: messagebox.showinfo("Help", doc))
        # view
        self.widget = widget_constructor(self, **widget_kwargs)
        self.columnconfigure(0, weight=1)
        self.widget.grid(row=1, column=0, sticky='ew', padx=5, pady=5)

    def _init_data(self, var_cls):
        return var_cls(master=self, name=self.text, value=self.default)

    def get_data(self):
        return self.data.get()


class IntEntry(Entry):
    def __init__(self, master: Page, text, default, doc, **kwargs):
        def _update_int_var(value):
            try:
                self.data.set(int(float(value)))  # Convert to integer
            except ValueError:
                pass  # Ignore non-integer values

        super().__init__(master, text, ttk.Frame, default, doc, **kwargs)
        # model-binding
        self.data = self._init_data(tk.IntVar)
        # view
        self.spinbox = ttk.Spinbox(self.widget, textvariable=self.data, from_=0, to=100, increment=1)
        self.spinbox.grid(row=0, column=0, padx=(0, 5))  # Adjust padx value
        self.slider = ttk.Scale(self.widget, from_=0, to=100, orient="horizontal", variable=self.data, command=_update_int_var)
        self.slider.grid(row=0, column=1, sticky="ew")  # Allow slider to expand horizontally


class FloatEntry(Entry):
    def __init__(self, master: Page, text, default, precision, doc, **kwargs):
        def _update_float_var(value):
            try:
                formatted_value = "{:.{}f}".format(float(value), self.precision)  # Format entered value
                self.data.set(float(formatted_value))
            except ValueError:
                pass

        super().__init__(master, text, ttk.Frame, default, doc, **kwargs)
        # model-binding
        self.precision = precision
        self.data = self._init_data(tk.DoubleVar)
        # view
        format_string = f"%.{precision}f"  # Adjust precision dynamically
        self.spinbox = ttk.Spinbox(self.widget, textvariable=self.data, from_=0, to=1, increment=0.01, format=format_string)
        self.spinbox.grid(row=0, column=0, padx=(0, 5))
        self.slider = ttk.Scale(self.widget, from_=0, to=1, orient="horizontal", variable=self.data, command=_update_float_var)
        self.slider.grid(row=0, column=1, sticky="ew")


class OptionEntry(Entry):
    def __init__(self, master: Page, text, options, default, doc, **kwargs):
        super().__init__(master, text, ttk.Combobox, default, doc, values=options, **kwargs)
        # model-binding
        self.options = []
        self.data = self._init_data(tk.StringVar)
        self.widget.set(default)


class Checkbox(Entry):
    def __init__(self, master: Page, text, default, doc, **kwargs):
        super().__init__(master, text, ttk.Checkbutton, default, doc, **kwargs)
        self.data = self._init_data(tk.BooleanVar)
        self.widget.configure(variable=self.data)


class TextEntry(Entry):
    def __init__(self, master: Page, text, default, doc, **kwargs):
        """there is no ttk.Text"""

        def _update_text(*args):
            self.data.set(self.widget.get("1.0", "end-1c"))

        super().__init__(master, text, tk.Text, default, doc, height=4, **kwargs)
        self.data = self._init_data(tk.StringVar)
        self.widget.bind("<<Modified>>", _update_text)
        self.widget.insert("1.0", default)


class Form(ttk.PanedWindow):
    """
    - accepts and creates navbar for input pages
    - layout: page-based navigation
    - filter: locate form entries by searching for title keywords
    """

    def __init__(self, master, pages: list[Page], *args, **kwargs):
        super().__init__(master)
        assert pages
        self.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Left panel: navigation bar with filtering support
        self.navPane = ttk.Frame(self, width=200)
        self.navPane.pack_propagate(False)  # Prevent the widget from resizing to its contents
        # Create a new frame for the search box and treeview
        search_box = ttk.Frame(self.navPane)
        search_box.pack(side="top", fill="x")
        self.searchEntry = ttk.Entry(search_box)
        self.searchEntry.pack(side="left", fill="x", expand=True)
        self.searchEntry.bind("<KeyRelease>", self.filter_entries)
        # Place the treeview below the search box
        self.tree = ttk.Treeview(self.navPane, show="tree")
        self.tree.heading("#0", text="", anchor="w")  # Hide the column header
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.update_entries)
        # Right panel: entries in page
        self.entryPane = ttk.Frame(self)
        # build form with navbar and page frame
        self.add(self.navPane, weight=0)
        self.add(self.entryPane, weight=1)
        # imp
        pg_titles = [pg.get_title() for pg in pages]
        self.pages = {title: pg for title, pg in zip(pg_titles, pages)}
        # Populate tree
        for title, pg in self.pages.items():
            self.tree.insert("", "end", text=title)
        # select first page
        self.pages[0].pack()
        self.tree.selection_set(tree.get_children()[0])

    def update_entries(self, event):
        selected_item = tree.focus()
        selected_title = tree.item(selected_item, "text")
        # Hide all groups
        for pg in self.pages:
            pg.pack_forget()
        self.pages[selected_title].pack()
        # After hiding, update the right pane to ensure correct display
        self.entryPane.update()

    def filter_entries(self, event):
        keyword = search_entry.get().strip().lower()
        for title, pg in self.pages.items():
            for entry in pg.winfo_children():
                assert isinstance(entry, Entry)
                if keyword not in entry.text.lower():
                    entry.pack_forget()
                    continue
                entry.pack(fill="x", padx=5, pady=5, anchor="w")
        self.entryPane.update()


def update_right_panel(event):
    global current_group

    selected_item = tree.focus()
    selected_title = tree.item(selected_item, "text")

    # Hide all groups
    for grp in (group1, group2, group3):
        grp.pack_forget()

    # Determine which group to show based on the selected title
    if selected_title == group1.cget("text"):
        current_group = group1
    elif selected_title == group2.cget("text"):
        current_group = group2
    elif selected_title == group3.cget("text"):
        current_group = group3

    # After hiding, update the right pane to ensure correct display
    right_frame.update()

    # Show the selected group, if any
    if current_group:
        current_group.pack()


def filter_widgets(event):
    keyword = search_entry.get().strip().lower()

    for group in [group1, group2, group3]:
        for widget in group.winfo_children():
            assert isinstance(widget, Entry)
            label_text = widget.label.cget("text").lower()
            if keyword in label_text:
                widget.pack(fill="x", padx=5, pady=5, anchor="w")
            else:
                widget.pack_forget()
    right_frame.update()


def submit_data():
    # Collect data from all the widgets in the groups
    data = {}
    for group in [group1, group2, group3]:
        for widget in group.winfo_children():
            if isinstance(widget, Entry):
                label = widget.label["text"]
                if isinstance(widget.widget, ttk.Checkbutton):
                    value = widget.widget.instate(["selected"])
                elif isinstance(widget.widget, tk.Text):
                    value = widget.widget.get("1.0", "end-1c")  # Get text content
                elif isinstance(widget.widget, (ttk.Spinbox, ttk.Scale)):
                    value = widget.widget.get()
                    try:
                        value = int(value)  # Try to convert to integer
                    except ValueError:
                        try:
                            value = float(value)  # Try to convert to float
                        except ValueError:
                            pass  # Cannot convert, leave as is
                else:
                    value = None

                if value is not None:
                    data[label] = value

    # Show the data as formatted JSON in a message box
    formatted_data = json.dumps(data, indent=4)
    if formatted_data.strip() == "{}":
        messagebox.showinfo("Submitted Data", "No data to submit.")
    else:
        messagebox.showinfo("Submitted Data", formatted_data)


root = tk.Tk()
root.title("Group Example")
screen_size = (root.winfo_screenwidth(), root.winfo_screenheight())
size = (800, 600)
root.geometry('{}x{}+{}+{}'.format(
    size[0],
    size[1],
    int(screen_size[0] / 2 - size[0] / 2),
    int(screen_size[1] / 2 - size[1] / 2))
)

# Main layout with PanedWindow
paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Left panel for the tree view and search box
left_frame = ttk.Frame(paned_window, width=200)
left_frame.pack_propagate(False)  # Prevent the widget from resizing to its contents

# Create a new frame for the search box and treeview
search_frame = ttk.Frame(left_frame)
search_frame.pack(side="top", fill="x")

search_entry = ttk.Entry(search_frame)
search_entry.pack(side="left", fill="x", expand=True)
search_entry.bind("<KeyRelease>", filter_widgets)

# Place the treeview below the search box
tree = ttk.Treeview(left_frame, show="tree")
tree.heading("#0", text="", anchor="w")  # Hide the column header

tree.pack(side="left", fill="both", expand=True)

# Right panel for displaying groups
right_frame = ttk.Frame(paned_window)

# Add frames to PanedWindow
paned_window.add(left_frame, weight=0)
paned_window.add(right_frame, weight=1)

# Creating groups
group1 = Page(right_frame, "Group 1")
group1.pack()

group2 = Page(right_frame, "Group 2")
group2.pack()

group3 = Page(right_frame, "Group 3")
group3.pack()

current_group = group1
# Adding widgets to groups
integer_widget = IntEntry(group1, "Integer Value", 10, "This is an integer value.")
float_widget = FloatEntry(group1, "Float Value", 0.5, 4, "This is a float value.")
option_widget = OptionEntry(group2, "Options", ["Option 1", "Option 2", "Option 3"], "Option 2", "This is an options widget.")
checkbox_widget = Checkbox(group2, "Checkbox", True, "This is a checkbox widget.")
text_widget = TextEntry(group3, "Text", "Lorem ipsum dolor sit amet", "This is a text widget.")
group1.add([integer_widget, float_widget])
group2.add([option_widget, checkbox_widget])
group3.add([text_widget])

# Populate tree
for group in [group1, group2, group3]:
    tree.insert("", "end", text=group.cget("text"))

tree.bind("<<TreeviewSelect>>", update_right_panel)
tree.selection_set(tree.get_children()[0])
update_right_panel(None)

# Create a frame for the bottom bar
bottom_bar_frame = ttk.Frame(root)
bottom_bar_frame.pack(side="bottom", fill="x")

# Create a separator line with a background color
separator = ttk.Separator(bottom_bar_frame, orient="horizontal")
separator.pack(fill="x")

# Create Cancel and Submit buttons
cancel_button = ttk.Button(bottom_bar_frame, text="Cancel", command=root.quit)
submit_button = ttk.Button(bottom_bar_frame, text="Submit", command=submit_data, cursor='hand2')

# Pack buttons with some padding
submit_button.pack(side="right", padx=10, pady=10)
cancel_button.pack(side="right", padx=10, pady=10)

# Bind the ENTER key to trigger the Submit button
root.bind("<Return>", submit_data)

# Bind the ESC key to quit the program
root.bind("<Escape>", lambda event: root.quit())

root.mainloop()
