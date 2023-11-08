import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfiledialog
import tkinter.font as tkfont
import tkinter.messagebox as tkmsgbox
# 3rd party
import kkpyutil as util


def create_root_window(title, size=None, resizable=(False, False), icon=None, onquit=None):
    """
    - Create a tkinter root window
    - show it at the center screen
    - caller must start mainloop afterward
    """
    def _unpin_root_on_focusin(event):
        """Solve the dilemma: root window hidden behind other apps on first run."""
        if type(event.widget).__name__ == 'Tk':
            event.widget.attributes('-topmost', False)

    def _quit_app():
        if callable(onquit):
            onquit()
        root.destroy()
    root = tk.Tk()
    root.title(title)
    if size is not None:
        screen_size = (root.winfo_screenwidth(), root.winfo_screenheight())
        root.geometry('{}x{}+{}+{}'.format(
            size[0],
            size[1],
            int(screen_size[0] / 2 - size[0] / 2),
            int(screen_size[1] / 2 - size[1] / 2))
        )
    root.resizable(width=resizable[0], height=resizable[1])
    # CAUTION: on macOS,
    # - icon won't show in window title
    # - it will be the dock image
    if icon:
        root.iconphoto(True, tk.PhotoImage(file=icon))
    root.clipboard_clear()
    root.attributes('-topmost', True)
    root.focus_force()
    root.bind('<FocusIn>', _unpin_root_on_focusin)
    root.protocol('WM_DELETE_WINDOW', _quit_app)
    root.bind('<Escape>', lambda e: _quit_app())
    return root


COLOR_PRIORITY_MAP = {
    'Common': 'gray93',
    'Action': 'gainsboro'
}


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


class ScrollFrame(tk.Frame):
    """
    - scrollable widget rack with a vertical layout
    - scrollable using right scrollbar.
    Usage:
        propPanel = ScrollFrame(parent)
        propPanel.frame.grid_rowconfigure(0, weight=1)
        propPanel.frame.grid_columnconfigure(0, weight=1)
        someWidget = SomeWidget(propPanel.frame)
        someWidget.grid(widgets=0, column=0, sticky='nsew')
        propPanel.pack(side="top", fill="both", expand=True)
    """
    def __init__(self, *args, **kwargs):
        def _configure_interior(event):
            # Update the scrollbars to match the size of the inner frame.
            width, height = (self.frame.winfo_reqwidth(),
                             self.frame.winfo_reqheight())
            self.canvas.config(scrollregion=(0, 0, width, height))
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=self.frame.winfo_reqwidth())

        def _configure_canvas(event):
            # update the inner frame's width to fill the canvas
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.itemconfigure(frame_id, width=self.canvas.winfo_width())
        super().__init__(*args, **kwargs)
        self.configure(padx=5)
        # data
        self.hiddenWgts = []
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0)
        self.frame = tk.Frame(self.canvas, bg=COLOR_PRIORITY_MAP['Common'], relief=tk.SUNKEN,
                              pady=5)
        self.scroll = tk.Scrollbar(
            self, orient='vertical', command=self.canvas.yview, bg='yellow'
        )
        self.canvas.config(yscrollcommand=self.scroll.set)
        frame_id = self.canvas.create_window(
            (0, 0), window=self.frame, anchor='nw'
        )
        self.frame.bind('<Configure>', _configure_interior)
        self.canvas.bind('<Configure>', _configure_canvas)
        # self.frame.bind('<Enter>', self._bound_to_mousewheel)
        # self.frame.bind('<Leave>', self._unbound_to_mousewheel)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def pack(self, *args, **kwargs):
        self.scroll.pack(side='right', fill='y', expand=False)
        self.canvas.pack(side='left', fill='both', expand=True)
        super().pack(*args, **kwargs)

    def filter_widgets(self, keyword, domains):
        """
        Search keyword in widget property domains, e.g., names or titles,
        and show only hit widgets. Case insensitive for now.
        :param keyword: User keywords
        :param domains: Among widget properties, where to look for keywords.
        :return:
        TODO
        - preference for case sensitivity.
        """
        # Make it case-insensitive
        keyword = keyword.lower()
        if empty_searchbar := keyword == '' or not domains:
            for child in self.hiddenWgts:
                child.grid(row=child.gridConfig['row'],
                           column=child.gridConfig['column'],
                           sticky=child.gridConfig['sticky'])
            self.hiddenWgts = []
            return
        for child in self.frame.winfo_children():
            # widget provides Getters for domain names.
            search_domains = [eval(f'child.get_{d.lower()}()', {'child': child}) for d in domains]
            # case-insensitive
            search_domains = [sd.lower() for sd in search_domains if sd is not None]
            to_hide = True
            for sd in search_domains:
                # Check next domain.
                if keyword not in sd:
                    continue
                # Show hidden widget again on search hit;
                # Stop searching
                if child in self.hiddenWgts:
                    to_hide = False
                    child.grid(row=child.gridConfig['row'],
                               column=child.gridConfig['column'],
                               sticky=child.gridConfig['sticky'])
                    # self.hiddenWidgets.remove(child)  # useless.
                    break
            if to_hide:
                child.grid_forget()
                self.hiddenWgts.append(child)
