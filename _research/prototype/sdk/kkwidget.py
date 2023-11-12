import json
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox as tkmsgbox
# 3rd party
import kkpyutil as util


class _Globals:
    root = None
    validateIntCmd = None
    validateFloatCmd = None
    progressQueue = queue.Queue()


def _validate_int(user_input, new_value, widget_name):
    return _validate_number(user_input, new_value, widget_name, int)


def _validate_float(user_input, new_value, widget_name):
    return _validate_number(user_input, new_value, widget_name, float)


def _validate_number(user_input, new_value, widget_name, data_type):
    # disallow anything but numbers in the input
    is_digit = new_value == '' or new_value.isdigit()
    if not is_digit:
        _Globals.root.bell()
        return False
    minval = data_type(_Globals.root.nametowidget(widget_name).config('from')[4])
    maxval = data_type(_Globals.root.nametowidget(widget_name).config('to')[4])
    if not (minval <= data_type(user_input) <= maxval):
        _Globals.root.bell()
        return False
    return True


class Prompt:
    """
    - must use within tkinter mainloop
    - otherwise will hang upon confirmation
    """

    def __init__(self, logger=None):
        self.logger = logger or util.glogger

    def info(self, msg, confirm=True):
        """Prompt with info."""
        self.logger.info(msg)
        if confirm:
            tkmsgbox.showinfo('Info', msg, icon='info')

    def warning(self, detail, advice, question='Continue?', confirm=True):
        """
        - for problems with minimum or no consequences
        - user can still abort, but usually no special handling is needed
        """
        msg = f"""\
Detail:
{detail}

Advice:
{advice}

{question if confirm else 'Will continue anyways'}"""
        self.logger.warning(msg)
        if not confirm:
            return True
        return tkmsgbox.askyesno('Warning', msg, icon='warning')

    def error(self, errclass, detail, advice, confirm=True):
        """
        - for problems with significant impact
        - program will crash immediately
        """
        msg = f"""\
Detail:
{detail}

Advice:
{advice}

Will crash"""
        self.logger.error(msg)
        if confirm:
            tkmsgbox.showerror('Error', msg, icon='error')
        raise errclass(msg)


class Page(ttk.LabelFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, text=title, **kwargs)
        self.grid_columnconfigure(0, weight=1)

    @staticmethod
    def add(entries):
        """
        - vertical layout
        """
        for entry in entries:
            entry.layout()

    def get_title(self):
        return self.cget('text')

    def layout(self):
        self.pack(fill="x", pady=5)


class Form(ttk.PanedWindow):
    """
    - accepts and creates navbar for input pages
    - layout: page-based navigation
    - filter: locate form entries by searching for title keywords
    - structure: Form > Page > Entry
    - instantiation: Form > Page (slave to form pane) > Entry (slave to page)
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, orient=tk.HORIZONTAL)
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
        self.pages = {}

    def layout(self):
        self.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def init(self, pages):
        """
        - pages must be created using entryPane as master
        """
        pg_titles = [pg.get_title() for pg in pages]
        self.pages = {title: pg for title, pg in zip(pg_titles, pages)}
        # Populate tree
        for title, pg in self.pages.items():
            self.tree.insert("", "end", text=title)
        # select first page
        self.tree.selection_set(self.tree.get_children()[0])
        self.update_entries(None)

    def update_entries(self, event):
        """
        - the first call is triggered at binding time? where nothing is selected yet
        - app must always create a group
        """
        selected_item = self.tree.focus()
        # selection will be blank on startup because no item is selected
        selected_title = self.tree.item(selected_item, "text")
        # Hide all groups
        for pg in self.pages.values():
            pg.pack_forget()
        # After hiding, update the right pane to ensure correct display
        self.pages[selected_title].layout() if selected_title else list(self.pages.values())[0].layout()
        self.entryPane.update()

    def filter_entries(self, event):
        keyword = self.searchEntry.get().strip().lower()
        for title, pg in self.pages.items():
            for entry in pg.winfo_children():
                assert isinstance(entry, Entry)
                if keyword not in entry.text.lower():
                    entry.pack_forget()
                    continue
                entry.layout()
        self.entryPane.update()


class Entry(ttk.Frame):
    """
    - used as user input, similar to CLI arguments
    - widget must belong to a group
    - groups form a tree to avoid overloading parameter panes
    - groups also improves SNR by prioritizing frequently-tweaked parameters
    - page is responsible for lay out entries
    """

    def __init__(self, master: Page, text, widget_constructor, default, doc, **widget_kwargs):
        super().__init__(master)
        self.text = text
        self.default = default
        # model-binding
        self.data = None
        # title
        self.label = ttk.Label(self, text=self.text)
        self.label.grid(row=0, column=0, sticky='w')
        self.label.bind("<Double-Button-1>", lambda e: tkmsgbox.showinfo("Help", doc))
        # field
        self.field = widget_constructor(self, **widget_kwargs)
        self.columnconfigure(0, weight=1)
        self.field.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        # context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Reset", command=self._reset)
        # maximize context-menu hitbox
        self.field.bind("<Button-2>", self.show_context_menu)
        self.label.bind("<Button-2>", self.show_context_menu)

    def _init_data(self, var_cls):
        return var_cls(master=self, name=self.text, value=self.default)

    def _reset(self):
        self.set_data(self.default)

    def get_data(self):
        return self.data.get()

    def set_data(self, value):
        self.data.set(value)

    def layout(self):
        self.pack(fill="both", expand=True, padx=5, pady=5, anchor="w")

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()


class FormMenu(tk.Menu):
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.fileMenu = tk.Menu(self, tearoff=False)
        self.fileMenu.add_command(label="Load Preset ...", command=self.load_preset)
        self.fileMenu.add_command(label="Save Preset ...", command=self.save_preset)
        self.fileMenu.add_command(label="Exit", command=self.quit)
        self.add_cascade(label="File", menu=self.fileMenu)
        self.controller = controller

    def init(self, window):
        window.configure(menu=self)

    def load_preset(self):
        preset = filedialog.askopenfilename(title="Load Preset", filetypes=[
            # tkinter openfile dialog filter does not accept middlename,
            # so *.preset.json won't work here
            ("Preset Files", "*.json"),
        ])
        if preset:
            self.controller.load(preset)

    def save_preset(self):
        preset = filedialog.asksaveasfilename(title="Save Preset", filetypes=[
            ("Preset Files", "*.preset.json"),
        ])
        if preset:
            self.controller.save(preset)

    def quit(self):
        self.master.quit()


class FormController:
    """
    - observe all entries and update model
    """

    def __init__(self, fm=None, model=None):
        self.form = fm
        self.model = model

    def update(self):
        self.model = {pg.get_title(): {entry.text: entry.get_data() for entry in pg.winfo_children()} for pg in self.form.pages.values()}

    def load(self, preset):
        """
        - model includes input and config
        - input is runtime data that changes with each run
        - only config will be saved/loaded as preset
        """
        config = util.load_json(preset)
        for title, page in self.form.pages.items():
            for entry in page.winfo_children():
                try:
                    entry.set_data(config[title][entry.text])
                except KeyError:
                    pass

    def save(self, preset):
        """
        - only config is saved
        - input always belongs to group "input"
        """
        self.update()
        config = {pg.get_title(): {entry.text: entry.get_data() for entry in pg.winfo_children()} for title, pg in self.form.pages.items() if title != "input"}
        util.save_json(preset, config)

    def reset(self):
        for pg in self.form.pages.values():
            for entry in pg.winfo_children():
                entry.set_data(entry.default)

    def submit(self, event=None):
        """
        - subclass this to implement custom logic
        """
        _Globals.progressQueue.put(('/start', 0, 'Processing ...'))
        self.update()
        # lambda wrapper ensures "self" is captured by threading as a context
        # otherwise ui thread still blocks
        threading.Thread(target=lambda: self.run_background(), daemon=True).start()
        # prompt = Prompt()
        # prompt.warning('You are calling base class', 'Subclass this!')

    def run_background(self):
        """
        - run in background thread to avoid blocking UI
        """
        for p in range(101):
            # Simulate a task
            time.sleep(0.1)
            _Globals.progressQueue.put(('/processing', p, f'Processing {p}%...'))
        _Globals.progressQueue.put(('/stop', 100, 'Completed!'))


class FormActionBar(ttk.Frame):
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # action logic
        self.controller = controller
        # Bind the ENTER key to trigger the Submit button
        root_win = self.controller.form.master
        root_win.bind("<Return>", self.controller.submit)
        # Bind the ESC key to quit the program
        root_win.bind("<Escape>", lambda event: root_win.quit())

        # occupy the entire width
        # new buttons will be added to the right
        self.resetBtn = ttk.Button(self, text="Reset", command=self.reset_entries)
        self.separator = ttk.Separator(self, orient="horizontal")
        # Create Cancel and Submit buttons
        self.cancelBtn = ttk.Button(self, text="Cancel", command=root_win.quit)
        self.submitBtn = ttk.Button(self, text="Submit", command=self.controller.submit, cursor='hand2')
        # layout: keep the order
        self.separator.pack(fill="x")
        # left-most must pack after separator to avoid occluding the border
        self.resetBtn.pack(side="left", padx=10, pady=5)
        self.submitBtn.pack(side="right", padx=10, pady=10)
        self.cancelBtn.pack(side="right", padx=10, pady=10)

    def layout(self):
        self.pack(side="bottom", fill="x")

    def submit(self, event=None):
        """for debugging only"""
        self.controller.update()
        formatted_data = json.dumps(self.controller.model, indent=4)
        tkmsgbox.showinfo("Submitted Data", formatted_data)

    def reset_entries(self, event=None):
        self.controller.reset()


class WaitBar(ttk.Frame):
    """
    - app must run in worker thread to avoid blocking UI
    - when using subprocess to run a blackbox task, use indeterminate mode cuz there is no way to pass progress back
    - protocol: tuple(stage, progress, description), where stage is program instruction, description is for display
    - TODO: use IPC for cross-language open-source tasks
    """

    def __init__(self, master, progress_queue, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.queue = progress_queue
        self.stage = tk.StringVar(name='stage', value='')
        self.bar = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.label = ttk.Label(self.bar, textvariable=self.stage, text='...', foreground='white', background='black')

    def layout(self):
        """
        - overlay label on top of bar
        """
        self.bar.pack(side="right", fill="x", expand=True)
        self.label.place(relx=0.5, rely=0.5, anchor='center')
        self.pack(side='bottom', fill='both', expand=False)

    def poll(self, wait_ms=50):
        """
        - app pushes special messages to mark progress start/stop
        """
        while self.queue.qsize():
            msg = self.queue.get(0)
            cmd = msg[0]
            if cmd == '/start':
                self.bar.start()
            elif cmd == '/stop':
                self.bar.stop()
            else:
                raise NotImplementedError(f'Unexpected progress instruction: {cmd}')
        self.after(wait_ms, self.poll)


class ProgressBar(WaitBar):
    def __init__(self, master, progress_queue, *args, **kwargs):
        super().__init__(master, progress_queue, *args, **kwargs)
        self.progress = tk.DoubleVar(name='progress', value=0.)
        self.bar.configure(variable=self.progress, mode='determinate')

    def poll(self, wait_ms=50):
        """
        - Periodically check for messages from worker thread.
        """
        while self.queue.qsize():
            try:
                cmd, value, text = self.queue.get_nowait()
                if cmd == '/start':
                    self.bar.start()
                elif cmd == '/stop':
                    self.bar.stop()
                elif cmd == '/processing':
                    self.progress.set(value)
                self.stage.set(text)  # Update the label text
            except queue.Empty:
                pass
        self.after(wait_ms, self.poll)


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
        self.spinbox = ttk.Spinbox(self.field, textvariable=self.data, from_=0, to=100, increment=1, validate='all', validatecommand=_Globals.validateIntCmd)
        self.spinbox.grid(row=0, column=0, padx=(0, 5))  # Adjust padx value
        self.slider = ttk.Scale(self.field, from_=0, to=100, orient="horizontal", variable=self.data, command=_update_int_var)
        # Allow slider to expand horizontally
        self.slider.grid(row=0, column=1, sticky="ew")


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
        self.spinbox = ttk.Spinbox(self.field, textvariable=self.data, from_=0.0, to=1.0, increment=0.01, format=format_string, validate='all', validatecommand=_Globals.validateFloatCmd)
        self.spinbox.grid(row=0, column=0, padx=(0, 5))
        self.slider = ttk.Scale(self.field, from_=0, to=1, orient="horizontal", variable=self.data, command=_update_float_var)
        self.slider.grid(row=0, column=1, sticky="ew")


class OptionEntry(Entry):
    def __init__(self, master: Page, text, options, default, doc, **kwargs):
        super().__init__(master, text, ttk.Combobox, default, doc, values=options, **kwargs)
        # model-binding
        self.options = []
        self.data = self._init_data(tk.StringVar)
        self.field.configure(textvariable=self.data, state='readonly')
        self.field.set(default)


class Checkbox(Entry):
    def __init__(self, master: Page, text, default, doc, **kwargs):
        super().__init__(master, text, ttk.Checkbutton, default, doc, **kwargs)
        self.data = self._init_data(tk.BooleanVar)
        self.field.configure(variable=self.data)


class TextEntry(Entry):
    def __init__(self, master: Page, text, default, doc, **kwargs):
        """there is no ttk.Text"""

        super().__init__(master, text, tk.Text, default, doc, height=4, **kwargs)
        self.data = self._init_data(tk.StringVar)
        # because the binding definition below will trigger callbacks
        # we must avoid feedback loop by setting this flag right before binding
        self._updatingModel = True
        self.field.bind("<<Modified>>", self._on_text_changed)
        self.data.trace_add("write", self._on_data_changed)
        self.field.insert("1.0", default)

    def set_data(self, value):
        super().set_data(value)
        self._on_data_changed()

    def _on_data_changed(self, *args):
        """
        - update view on model changes
        """
        self._updatingModel = True
        seen = self.field.get("1.0", tk.END).strip()
        to_see = self.data.get()
        if seen != to_see:
            self.field.delete("1.0", tk.END)
            self.field.insert("1.0", to_see)
        self._updatingModel = False

    def _on_text_changed(self, event):
        """
        - update model on user editing
        - must avoid feedback loop when text changes are caused by model changes
        """
        if self._updatingModel:
            return
        self.data.set(self.field.get("1.0", tk.END))
        self.field.edit_modified(False)


def _test():
    _Globals.root = tk.Tk()
    _Globals.root.title("Group Example")
    screen_size = (_Globals.root.winfo_screenwidth(), _Globals.root.winfo_screenheight())
    size = (800, 600)
    _Globals.root.geometry('{}x{}+{}+{}'.format(
        size[0],
        size[1],
        int(screen_size[0] / 2 - size[0] / 2),
        int(screen_size[1] / 2 - size[1] / 2))
    )
    _Globals.validateIntCmd = (_Globals.root.register(_validate_int), '%P', '%S', '%W')
    _Globals.validateFloatCmd = (_Globals.root.register(_validate_float), '%P', '%S', '%W')
    form = Form(_Globals.root)
    form.layout()
    ctrlr = FormController(form)
    menu = FormMenu(_Globals.root, ctrlr)
    menu.init(_Globals.root)
    # Creating groups
    pg1 = Page(form.entryPane, "Group 1")
    pg1.layout()
    pg2 = Page(form.entryPane, "Group 2")
    pg2.layout()
    pg3 = Page(form.entryPane, "Group 3")
    pg3.layout()
    # Adding widgets to groups
    integer_widget = IntEntry(pg1, "Integer Value", 10, "This is an integer value.")
    float_widget = FloatEntry(pg1, "Float Value", 0.5, 4, "This is a float value.")
    option_widget = OptionEntry(pg2, "Options", ["Option 1", "Option 2", "Option 3"], "Option 2", "This is an options widget.")
    checkbox_widget = Checkbox(pg2, "Checkbox", True, "This is a checkbox widget.")
    text_widget = TextEntry(pg3, "Text", "Lorem ipsum dolor sit amet", "This is a text widget.")
    pg1.add([integer_widget, float_widget])
    pg2.add([option_widget, checkbox_widget])
    pg3.add([text_widget])
    form.init([pg1, pg2, pg3])
    form.layout()
    action_bar = FormActionBar(_Globals.root, ctrlr)
    action_bar.layout()
    progress_bar = ProgressBar(_Globals.root, _Globals.progressQueue)
    progress_bar.layout()
    progress_bar.poll()
    _Globals.root.mainloop()


if __name__ == "__main__":
    _test()
