import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class LabeledWidget(ttk.Frame):
    def __init__(self, master, label, widget_constructor, doc, **widget_kwargs):
        super().__init__(master)

        self.columnconfigure(0, weight=1)

        self.label = ttk.Label(self, text=label)
        self.label.grid(row=0, column=0, sticky='w')
        self.label.bind("<Double-Button-1>", lambda e: messagebox.showinfo("Help", doc))

        self.widget = widget_constructor(self, **widget_kwargs)
        self.widget.grid(row=1, column=0, sticky='ew', padx=5, pady=5)


class IntegerWidget(LabeledWidget):
    def __init__(self, master, label, default_value, doc, **kwargs):
        super().__init__(master, label, ttk.Entry, doc, **kwargs)
        self.widget.insert(0, str(default_value))


class FloatWidget(LabeledWidget):
    def __init__(self, master, label, default_value, doc, **kwargs):
        super().__init__(master, label, ttk.Entry, doc, **kwargs)
        self.widget.insert(0, str(default_value))


class OptionWidget(LabeledWidget):
    def __init__(self, master, label, options, default_value, doc, **kwargs):
        super().__init__(master, label, ttk.Combobox, doc, values=options, **kwargs)
        self.widget.set(default_value)


class CheckboxWidget(LabeledWidget):
    def __init__(self, master, label, default_value, doc, **kwargs):
        super().__init__(master, label, ttk.Checkbutton, doc, variable=tk.BooleanVar(value=default_value), **kwargs)


class TextWidget(LabeledWidget):
    def __init__(self, master, label, default_text, doc, **kwargs):
        super().__init__(master, label, tk.Text, doc, height=4, **kwargs)
        self.widget.insert("1.0", default_text)


class GroupWidget(ttk.LabelFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, text=title, **kwargs)
        self.grid_columnconfigure(0, weight=1)

    def add_widget(self, widget):
        widget.pack(fill="x", padx=5, pady=5, anchor="w")


def update_right_panel(event):
    global current_group

    selected_item = tree.focus()
    selected_title = tree.item(selected_item, "text")

    if current_group:
        current_group.pack_forget()

    if selected_title == group1.cget("text"):
        current_group = group1
    elif selected_title == group2.cget("text"):
        current_group = group2
    elif selected_title == group3.cget("text"):
        current_group = group3

    if current_group:
        current_group.pack(fill="x", pady=5)


current_group = None
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

# Left panel for the tree view
left_frame = ttk.Frame(paned_window, width=200)
left_frame.pack_propagate(False)  # Prevent the widget from resizing to its contents

# Right panel for displaying groups
right_frame = ttk.Frame(paned_window)

# Add frames to PanedWindow
paned_window.add(left_frame, weight=0)
paned_window.add(right_frame, weight=1)

tree = ttk.Treeview(left_frame)
tree.pack(side="left", fill="y", expand=True)

# Creating groups
group1 = GroupWidget(right_frame, "Group 1")
group1.pack(fill="x", pady=5)

group2 = GroupWidget(right_frame, "Group 2")
group2.pack(fill="x", pady=5)

group3 = GroupWidget(right_frame, "Group 3")
group3.pack(fill="x", pady=5)

# Adding widgets to groups
integer_widget = IntegerWidget(group1, "Integer Value", 10, "This is an integer value.")
group1.add_widget(integer_widget)

float_widget = FloatWidget(group1, "Float Value", 0.5, "This is a float value.")
group1.add_widget(float_widget)

option_widget = OptionWidget(group2, "Options", ["Option 1", "Option 2", "Option 3"], "Option 2", "This is an options widget.")
group2.add_widget(option_widget)

checkbox_widget = CheckboxWidget(group2, "Checkbox", True, "This is a checkbox widget.")
group2.add_widget(checkbox_widget)

text_widget = TextWidget(group3, "Text", "Lorem ipsum dolor sit amet", "This is a text widget.")
group3.add_widget(text_widget)

# Populate tree
for group in [group1, group2, group3]:
    tree.insert("", "end", text=group.cget("text"))

tree.bind("<<TreeviewSelect>>", update_right_panel)
tree.selection_set(tree.get_children()[0])
update_right_panel(None)

root.mainloop()
