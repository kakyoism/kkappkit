#!/usr/bin/env python

"""
Widget lib and factory functions based on pure Tkinter.

# TODO:
# - Explorer.
"""

# Import project modules.
import sys
import collections
import copy
import os
from os.path import dirname, exists, join, normpath, splitext
import pathlib
import platform

# Import 3rd-party modules.
if sys.version_info.major < 3:
    import Tkinter as tk
    import Tkinter.ttk as ttk
    import tkfiledialog as tkfiledialog
    import tkFont as tkfont
    import tkMessageBox as tkmsgbox
else:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.filedialog as tkfiledialog
    import tkinter.font as tkfont
    import tkinter.messagebox as tkmsgbox
import webbrowser


# Import project modules.
import util


# Metadata
__author__ = "Beinan Li"
__copyright__ = "Copyright $year$, Beinan Li"
__credits__ = ["Beinan Li"]
__license__ = "MIT"
__maintainer__ = "Beinan Li"
__email__ = "li.beinan@gmail.com"
__version__ = "0.6.6"


#
# Globals
#
_script_dir = normpath(dirname(__file__))
FULL_EXPAND = 'nsew'
_logger = util.build_logger(__file__)
COLOR_LAYERS = {
    'Common': 'gray93',
    'Action': 'gainsboro'
}


class Prompt:
    """
    Prompt user and also log to the log file.
    It supports GUI and CLI modes.
    """
    def __init__(self, logger=None, is_gui=True):
        self.logger = logger
        self.is_gui = is_gui

    def info(self, msg):
        """Prompt with info."""
        if self.is_gui:
            tkmsgbox.showinfo('Info', msg, icon='info')
        if self.logger is not None:
            self.logger.info(msg)

    def warning(self, desc, causes, suggestions, confirm=False):
        """
        Prompt with warning and details.
        :param desc: One liner description.
        :param causes: Possible causes of the issue.
        :param suggestions: Suggested actions.
        :param confirm: If True, user has chance to bail, False otherwise.
        :return True or False if confirm is True:
        """
        epilog = 'Continue anyways?' \
            if confirm else 'But I\'ll continue for now.'
        msg = """
{}.

Possible Causes:
{}

Suggestions:
{}

{}
        """.format(desc,
                   '\n- '.join([''] + causes),
                   '\n- '.join([''] + suggestions),
                   epilog)
        if self.logger is not None:
            self.logger.warning(msg)
        if self.is_gui:
            prompt = tkmsgbox.askyesno if confirm else tkmsgbox.showwarning
            res = prompt('Warning', msg, icon='warning')
        else:
            # Question is epilog above.
            res = util.query_yes_no('', default=False)
        return res

    def error(self, desc, causes, suggestions, confirm=False):
        """
        Prompt with warning and details.
        :param desc: One liner description.
        :param causes: Possible causes of the issue.
        :param suggestions: Suggested actions.
        :param confirm: If True, user has chance to bail, False otherwise.
        :return True or False if confirm is True:
        """
        epilog = '\nContinue anyways?' \
            if confirm else '\nBut I\'ll continue for now.'
        msg = """
{}.

Possible Causes:
{}

Suggestions:
{}

{}
        """.format(desc,
                   '\n- '.join([''] + causes),
                   '\n- '.join([''] + suggestions),
                   epilog)
        if self.logger is not None:
            self.logger.warning(msg)
        if self.is_gui:
            prompt = tkmsgbox.askyesno if confirm else tkmsgbox.showerror
            res = prompt('Warning', msg, icon='error')
        else:
            # Question is epilog above.
            res = util.query_yes_no('', default=False)
        return res


def unpin_root_on_focus_in(event):
    """Solve the dilemma: root window hidden behind other apps on first run."""
    if type(event.widget).__name__ == 'Tk':
        event.widget.attributes('-topmost', False)


def get_widget_path(widget):
    """
    Get widget full path assembled by all its ancestor widgets' names
    down to its own.
    """
    return str(widget)


class ScrollFrame(tk.Frame):
    """
    Left child frame acts as a vertical widget rack,
    scrollable using right scrollbar.
    Usage:
        propPanel = ScrollFrame(parent)
        propPanel.frame.grid_rowconfigure(0, weight=1)
        propPanel.frame.grid_columnconfigure(0, weight=1)
        someWidget = SomeWidget(propPanel.frame)
        someWidget.grid(widgets=0, column=0, sticky='nsew')
        propPanel.pack(side="top", fill="both", expand=True)
    """
    def __init__(self, *args, **kwargs):
        """
        tk.Frame.__init__(self, master=None, cnf={}, **kw):
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.configure(padx=5)
        # data
        self.hiddenWidgets = []
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0)
        self.frame = tk.Frame(self.canvas, bg=COLOR_LAYERS['Common'], relief=tk.SUNKEN,
                              pady=5)
        self.scroll = tk.Scrollbar(
            self, orient='vertical', command=self.canvas.yview, bg='yellow'
        )
        self.canvas.config(yscrollcommand=self.scroll.set)
        frame_id = self.canvas.create_window(
            (0, 0), window=self.frame, anchor='nw'
        )

        def _configure_interior(event):
            # Update the scrollbars to match the size of the inner frame.
            width, height = (self.frame.winfo_reqwidth(),
                             self.frame.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 {} {}".format(width, height))
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=self.frame.winfo_reqwidth())
        self.frame.bind('<Configure>', _configure_interior)
        # self.frame.bind('<Enter>', self._bound_to_mousewheel)
        # self.frame.bind('<Leave>', self._unbound_to_mousewheel)

        def _configure_canvas(event):
            # update the inner frame's width to fill the canvas
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.itemconfigure(frame_id,
                                          width=self.canvas.winfo_width())
        self.canvas.bind('<Configure>', _configure_canvas)

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
        keyword = keyword.lower()  # Make it case insensitive.
        if keyword == '' or not domains:  # Empty search bar.
            for child in self.hiddenWidgets:
                child.grid(row=child.gridConfig['row'],
                           column=child.gridConfig['column'],
                           sticky=child.gridConfig['sticky'])
            self.hiddenWidgets = []
            return
        for child in self.frame.winfo_children():
            # print('Name: {}; Title: {}; Help: {}'.format(
            # child._name, child.widgets['Title']['text']
            # if 'Title' in child.widgets.keys()
            # else '(No Title)', child.handlers['OnHelp']))

            # Every widget provides Getters for domain names.
            where_to_search = [
                eval('child.get_{}()'.format(d.lower()), {'child': child})
                for d in domains
            ]
            where_to_search = [
                x.lower() for x in where_to_search if x is not None
            ]  # case-insensitive
            to_hide = True
            for where in where_to_search:
                # Check next domain.
                if keyword not in where:
                    continue
                # Show it again on search hit;
                # Stop searching.
                if child in self.hiddenWidgets:
                    to_hide = False
                    child.grid(row=child.gridConfig['row'],
                               column=child.gridConfig['column'],
                               sticky=child.gridConfig['sticky'])
                    # self.hiddenWidgets.remove(child)  # useless.
                    break
            if to_hide:
                child.grid_forget()
                self.hiddenWidgets.append(child)


class ConfigMan:
    """
    Load/Save app parameters from/to config files: main and default.
    """
    def __init__(self, app_dir, *args, **kwargs):
        self.app_dir = app_dir
        cfg_file = join(app_dir, util.MAIN_CFG_FILENAME)
        self.config = util.load_json(cfg_file) if exists(cfg_file) else {}

    def load(self):
        cfg_file = join(self.app_dir, util.MAIN_CFG_FILENAME)
        self.config = util.load_json(cfg_file) if exists(cfg_file) else {}
        return self.config

    def load_default(self):
        cfg_file = join(self.app_dir, util.DEFAULT_CFG_FILENAME)
        self.config = util.load_json(cfg_file) if exists(cfg_file) else {}
        return self.config

    def load_from(self, path):
        self.config = util.load_json(path) if exists(path) else {}
        return self.config

    def save(self):
        util.save_json(join(self.app_dir, util.MAIN_CFG_FILENAME), self.config)

    def save_as(self, path):
        util.save_json(path, self.config)

    def save_default(self):
        util.save_json(join(self.app_dir, util.DEFAULT_CFG_FILENAME),
                       self.config)

    def update_from_widgets(self, widgets):
        """
        Update config fields with widget data.
        No key-error guard, assuming widget names are keys read from config,
        and config files don't change via external editor while running.
        """
        for w, wgt in enumerate(widgets):
            if hasattr(wgt, 'input'):
                self.config[wgt.get_name()]['Value'] = wgt.get_data()

    def update_widgets(self, widgets):
        """
        Update widget data with config fields. Prompt upon key errors.
        """
        for w, wgt in enumerate(widgets):
            if hasattr(wgt, 'input'):
                if wgt.get_name() not in self.config.keys():
                    tkmsgbox.showerror(
                        title='KeyError',
                        message="""
    Widget name 

        {}

    is an invalid config key. So widget won't be updated.

    Cause: 
        Someone renamed the top-level key in one of the config files. 

    Solution: 
        - Contact programmer to sync up code with the new key, or ...
        - Rename the top-level key in all config files using widget name: {}.
    """.format(wgt.get_name(), wgt.get_name()), icon=tkmsgbox.ERROR)
                wgt.set_data(self.config[wgt.get_name()])


class WidgetBase(tk.Frame):
    """Base class of all widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(bd=0)
        self.widgets = collections.OrderedDict()
        self.gridWeights = {}  # Proportions of children along the widgets.
        self.gridConfig = {}  # For keyword-based widget filtering.

    def get_name(self):
        """Accessor for widget show/hide keyword search algorithm."""
        return self._name

    def get_help(self):
        """Accessor for widget show/hide keyword search algorithm."""
        return None

    def get_title(self):
        """Accessor for widget show/hide keyword search algorithm."""
        return None

    def configure_internal(self, config):
        """
        Extend to configure frame appearance.
        :param config: {'property': value, ...} as extended properties.
        """
        for k, v in config.items():
            self[k] = v

    def pack(self, *args, **kwargs):
        """Pack children left aligned and allow them to expand with parent."""
        for k, v in self.widgets.items():
            v.pack(side='left', fill='both', expand=True)
        super().pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        """Layout child widgets within the only child frame."""
        self.grid_rowconfigure(0, weight=1)  # Layout one widgets.
        # Main widgets
        col = 0
        for k, v in self.widgets.items():  # Layout each column.
            self.grid_columnconfigure(col, weight=self.gridWeights[k])
            v.grid(row=0, column=col, sticky=FULL_EXPAND)
            col += 1
        super().grid(*args, **kwargs)
        self.gridConfig = kwargs  # Save for restoring grid prop during search.


class Separator(WidgetBase):
    """Visual separator."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(bg=COLOR_LAYERS['Common'], padx=5, pady=10)
        self.widgets['Separator'] = ttk.Separator(self)
        self.gridWeights['Separator'] = 1

    def __repr__(self):
        return '{}: Visual gap, non-interactive.'.format(type(self).__name__)

    def get_name(self):
        return self._name


class TitleStrip(WidgetBase):
    """Row with label and separator. It defines the purpose of rows below it."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(bg=COLOR_LAYERS['Common'], pady=10)
        # Widgets
        self.widgets['Head'] = ttk.Separator(self)
        self.widgets['Title'] = ttk.Label(self, text='Title',
                                          font=tkfont.Font(size=14,
                                                           weight='bold'))
        self.widgets['Tail'] = ttk.Separator(self)
        self.gridWeights['Head'] = 100
        self.gridWeights['Title'] = 1
        self.gridWeights['Tail'] = 100

    def __repr__(self):
        return '{}: not interactive.'.format(type(self).__name__)

    def configure_internal(self, config):
        """
        Extend to configure title text properties.
        :param config: {'property': value} about appearance, data range, etc.
        :return:
        """
        self.widgets['Title']['text'] = config['Title']
        for k, v in filter(lambda kv: kv[0] != 'Title', config.items()):
            self.widgets['Title'][k] = v

    def get_title(self):
        return self.widgets['Title']['text']

    def pack(self, *args, **kwargs):
        for k, v in self.widgets.items():
            v.pack(side='left', fill='both', expand=True)
        super().pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        """Layout child widgets within the only child frame."""
        self.grid_rowconfigure(0, weight=1)
        # Main widgets
        col = 0
        for k, v in self.widgets.items():  # Layout each column.
            self.grid_columnconfigure(col, weight=self.gridWeights[k])
            v.grid(row=0, column=col, sticky=FULL_EXPAND)
            col += 1
        super().grid(*args, **kwargs)
        self.gridConfig = kwargs


class InfoStrip(WidgetBase):
    """Show read-only descriptions. Add scrollbar only if multiline."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Widgets
        self.widgets['Title'] = ttk.Label(self, text='Title')
        self.widgets['Content'] = tk.Message(self, text='', justify=tk.LEFT,
                                             anchor='w',
                                             width=1000,
                                             bg=COLOR_LAYERS['Common'])
        self.gridWeights['Title'] = 1
        self.gridWeights['Content'] = 100

    def __repr__(self):
        return '{}: not interactive.'.format(type(self).__name__)

    def configure_internal(self, config):
        """
        Extend to configure title text properties.
        :param config: {'property': value} about appearance, data range, etc.
        :return:
        """
        self.widgets['Title']['text'] = config['Title']
        self.widgets['Content']['text'] = config['Value']

    def get_title(self):
        return self.widgets['Title']['text']

    def pack(self, *args, **kwargs):
        for k, v in self.widgets.items():
            v.pack(side='left', fill='both', expand=True)
        super().pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        """Layout child widgets within the only child frame."""
        self.grid_rowconfigure(0, weight=1)
        # Main widgets
        col = 0
        for k, v in self.widgets.items():  # Layout each column.
            self.grid_columnconfigure(col, weight=self.gridWeights[k])
            v.grid(row=0, column=col, sticky=FULL_EXPAND)
            col += 1
        super().grid(*args, **kwargs)
        self.gridConfig = kwargs


class RowStrip(WidgetBase):
    """
    A compound widget as a parameter config UI.

    Features
    - Preserves Tkinter's init-configure-layout-callback paradigm;
    - Adds UI to reset data to its default value, with user hooks to
    retrieve default values.
    - Adds Provides UI to open help about the data, provided in config file.

    Usecases
    - Programmer defines control parameters for CLI script in a
    JSON config file, including default values and help docs of the parameter.
    - Programmer then generates UI for the parameter using generic factory
    method. The factory method stack up these row-strips.
    - Programmer ships package containing the CLI script including UI
    generator code, and JSON config files as a standalone app.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input = None  # To implement in children
        self.widgets = collections.OrderedDict()
        self.gridWeights = {}  # Proportions of children along the widgets.
        self.gridConfig = {}
        # Common widgets
        self.reset = ttk.Button(self, text='Reset', command=self._on_reset)
        self.help = ttk.Button(self, text='?', command=self._on_help)
        self.handlers = {k: None for k in ['OnReset',
                                           'OnHelp',
                                           'OnChange']}

    def __repr__(self):
        return 'class: {}, name: {}: data: {}'.format(
            self.__class__.__name__, self._name, self.get_data())

    def pack(self, *args, **kwargs):
        """Pack child widgets in a row."""
        for k, v in self.widgets.items():
            v.pack(side='left', fill='both', expand=True)
        self.help.pack(side='right', fill='both', expand=False)
        self.reset.pack(side='right', fill='both', expand=False)
        super().pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        """
        Pack child widgets by find portions,
        and preserve grid config for restoring upon UI filtering.
        """
        self.grid_rowconfigure(0, weight=1)  # Layout single widgets.
        # Main widgets
        col = 0
        for k, v in self.widgets.items():  # Layout each column.
            self.grid_columnconfigure(col, weight=self.gridWeights[k])
            v.grid(row=0, column=col, sticky=FULL_EXPAND)
            col += 1
        # Common widgets
        self.grid_columnconfigure(col, weight=1)
        self.reset.grid(row=0, column=col, sticky='nsw')  # right-aligned.
        # Disable button if no callback is assigned.
        if not callable(self.handlers['OnReset']):
            self.reset.configure(state=tk.DISABLED)
        col += 1
        self.grid_columnconfigure(col, weight=1)
        self.help.grid(row=0, column=col, sticky='nsw')  # right-aligned.
        if not callable(self.handlers['OnHelp']):
            self.help.configure(state=tk.DISABLED)
        col += 1
        super().grid(*args, **kwargs)
        self.gridConfig = kwargs

    def get_data(self):
        """Return user input data to assign to a named parameter."""
        return self.input.get() if self.input is not None else None

    def set_data(self, kvp):
        """
        Update widgets based on new kvp data field.
        :param kvp: field retrieved using self._name from config.
        """
        self.input.set(kvp['Value'])

    def get_help(self):
        if callable(self.handlers['OnHelp']):
            return self.handlers['OnHelp'](self)  # Get help text from app.
        return None

    def get_title(self):
        return self.widgets['Title']['text'] \
               if 'Title' in self.widgets.keys() else None

    def bind_internal(self, eventmaps):
        """
        Register events and handlers. Support cookies.
        :param eventmaps: {'on_xx": handler_func} for client logic.
        to use.
        :return:
        """
        for k, v in eventmaps.items():
            self.handlers[k] = v

        # Bind var observer: lambda to pass:
        # - widget for accessing data
        # - vars specified by trace.
        if callable(self.handlers['OnChange']):
            self.input.trace(
                mode='w',
                callback=lambda *args: self.handlers['OnChange'](self, *args)
            )

    def _on_reset(self):
        # Reset widget data to default based on configuration.
        if callable(self.handlers['OnReset']):
            # if self.reset['state'] != tk.DISABLED:
            default = self.handlers['OnReset'](self._name)  # Get default from
            # app.
            self.set_data(default)

    def _on_help(self):
        """Show user docs in a separate window."""
        if callable(self.handlers['OnHelp']):
            help_text = self.handlers['OnHelp'](self._name)  # Get help text
            # from app.
            window = tk.Toplevel(self)
            window.title('Help: {}'.format(self._name))
            text = tk.Text(window)
            text.insert(tk.INSERT, help_text)
            text.pack()


class EntryStrip(RowStrip):
    """Get info from app on pressing action button, and show it."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input = tk.StringVar(name=self._name, value='...')
        self.widgets['Title'] = ttk.Label(self, text='Title: ')
        self.widgets['Entry'] = ttk.Entry(self, textvariable=self.input)
        self.widgets['Action'] = ttk.Button(self, text='Action')
        self.widgets['Action'].configure(command=self._on_action)
        self.gridWeights['Title'] = 1
        self.gridWeights['Entry'] = 1000
        self.gridWeights['Action'] = 1
        self.handlers['OnAction'] = None

    def configure_internal(self, config):
        self.input.set(config['Value'])
        self.widgets['Title']['text'] = config['Title']
        if 'Action' in config.keys():
            self.widgets['Action']['text'] = config['Action']
            # Rule: bind action based on action type field in config.
            action_maps = {
                'Copy': self._copy_to_clipboard
            }
            for k, v in action_maps.items():
                if config['Action'].startswith(k):
                    self.handlers['OnAction'] = v
                    break
        super().configure_internal({})

    def _on_action(self):
        if callable(self.handlers['OnAction']):
            self.handlers['OnAction']()

    def _copy_to_clipboard(self):
        # Copy current path to clipboard.
        root = self.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(self.get_data())


class PreciseScale(ttk.Scale):
    """ ttk.Scale sublass that limits the precision of values. """
    def __init__(self, *args, **kwargs):
        self.precision = kwargs.pop('precision')  # Remove non-std kwarg.
        self.onChange = kwargs.pop('command', lambda *a: None)  # User callback.
        super().__init__(*args, command=self._value_changed, **kwargs)

    def _value_changed(self, new_value):
        new_value = round(float(new_value), self.precision)
        self.winfo_toplevel().globalsetvar(self.cget('variable'), new_value)
        self.onChange(new_value)  # Call user specified function.


class NumberStrip(RowStrip):
    """Get number from user input, and show it."""
    def __init__(self, *args, datatype='float', precision=3, **kwargs):
        super().__init__(*args, **kwargs)
        self.input = tk.IntVar(name=self._name, value=0) \
            if datatype == 'int' else tk.DoubleVar(name=self._name, value=0.)
        self.widgets['Title'] = ttk.Label(self, text='Number: ')
        self.widgets['Spin'] = tk.Spinbox(self,
                                          textvariable=self.input,
                                          wrap=True)
        self.widgets['Slider'] = PreciseScale(self,
                                              variable=self.input,
                                              orient=tk.HORIZONTAL,
                                              precision=precision)
        self.gridWeights['Title'] = 1
        self.gridWeights['Spin'] = 1
        self.gridWeights['Slider'] = 100

    def configure_internal(self, config):
        self.input.set(config['Value'])
        self.widgets['Title']['text'] = config['Title']
        # CAUTION: Must assign 'to' before 'from',
        # because 'from' might risk getting set bigger than 'to' any other way.
        self.widgets['Spin']['to'] = config['Range'][1]
        self.widgets['Spin']['from'] = config['Range'][0]
        self.widgets['Spin']['increment'] = config['Steps'][0]
        self.widgets['Slider']['to'] = config['Range'][1]
        self.widgets['Slider']['from'] = config['Range'][0]
        # Fit spinbox size to value range
        char_count = len(str(self.widgets['Spin']['to']))
        self.widgets['Spin'].configure(width=max(char_count+1, 6))

        # CAUTION: ttk.Scale has no increment or resolution
        # Set slider increment to int to avoid float increment when data is int.
        if isinstance(self.input, tk.IntVar):
            self.widgets['Slider']['command'] = self._int_increment
        elif isinstance(self.input, tk.DoubleVar):
            self.widgets['Slider'].precision = config['Precision'] \
                if 'Precision' in config.keys() else 3
        else:
            raise NotImplementedError("""
Unsupported var type: {}, expected tk.IntVar or tk.DoubleVar.
""".format(type(self.input)))

    def _int_increment(self, evt=None):
        """If slider generates floating point, lets round it up."""
        data = self.widgets['Slider'].get()
        if int(data) != data:
            self.widgets['Slider'].set(round(data))

    def _float_increment(self, evt=None):
        data = self.widgets['Slider'].get()
        if int(data) != data:
            self.widgets['Slider'].set(round(data))


class CheckStrip(RowStrip):
    """Checkbox with description."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input = tk.BooleanVar(name=self._name, value=True)
        self.widgets['Check'] = ttk.Checkbutton(self, text='',
                                                variable=self.input)
        self.widgets['Title'] = ttk.Label(self, text='To enable that Thingy!')
        self.gridWeights['Check'] = 1
        self.gridWeights['Title'] = 1000

    def configure_internal(self, config):
        self.input.set(config['Value'])  # Both True/False and 1/0 work.
        self.widgets['Title']['text'] = config['Title']


class OptionStrip(RowStrip):
    """Single selection through dropdown list."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input = tk.StringVar(master=self, name=self._name, value='')
        # OptionMenu widget does not save the list. So we must.
        self.options = []
        self.widgets['Title'] = ttk.Label(self, text='Select: ')
        self.widgets['Option'] = ttk.OptionMenu(self,
                                                self.input,
                                                '',
                                                *self.options)
        self.gridWeights['Title'] = 1
        self.gridWeights['Option'] = 1000

    def configure_internal(self, config):
        self.options = copy.deepcopy(config['Options'])
        self.input.set(config['Options'][config['Value']])
        self.widgets['Title']['text'] = config['Title']
        # CAUTION: must set default (Arg #3 ) before giving the option list.
        self.widgets['Option'] = ttk.OptionMenu(self,
                                                self.input,
                                                self.options[0],
                                                *self.options)

    def get_data(self):
        """
        Return the list index of the option string to save to config.
        """
        return self.options.index(self.input.get())

    def set_data(self, kvp):
        text = kvp['Options'][kvp['Value']]
        self.input.set(text)


class PathStrip(EntryStrip):
    """Open or save to a path, with filetype filers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filetypes = []
        self.defaultextension = '*.*'

    def configure_internal(self, config):
        super().configure_internal(config)
        self.filetypes = config['FileTypes']
        # Take head of file types; Remove * from *.jpg
        self.defaultextension = config['FileTypes'][0][1][1:]
        # Rule: bind action based on action type field in config.
        action_maps = {
            'Browse': self._browse,
            'Copy': super()._copy_to_clipboard
        }
        for k, v in action_maps.items():
            if config['Action'].startswith(k):
                self.handlers['OnAction'] = v
                break

    def _browse(self):
        # Update path from browsing.
        if platform.platform() in ('Windows', 'Linux'):
            data = tkfiledialog.askopenfilename(
                title='Select {}'.format(self.widgets['Title']['text']),
                filetypes=self.filetypes,
                defaultextension=self.defaultextension
            )
        else:
            data = tkfiledialog.askopenfilename(
                title='Select {}'.format(self.widgets['Title']['text'])
            )
        # CAUTION: tkFileDialog returns empty str on cancelling
        if data != '':
            self.input.set(data)


class ProgressStrip(tk.Frame):
    """
    Show progress with text and bar. Support determined and indefinite modes.
    """
    def __init__(self, *args, queue=None, mode='determinate', **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(bg=COLOR_LAYERS['Common'], padx=20)
        # data
        self.queue = queue
        self.progress = tk.DoubleVar(name='progress', value='0.')
        self.stage = tk.StringVar(name='stage', value='')
        # widgets
        self.widgets = collections.OrderedDict()
        self.widgets['Progress'] = ttk.Progressbar(self,
                                                   mode=mode,
                                                   orient='horizontal',
                                                   length=380)
        self.widgets['Stage'] = ttk.Label(self,
                                          textvariable=self.stage,
                                          width=200,
                                          anchor='e')
        self.gridWeights = {'Progress': 1, 'Stage': 1000}
        self.gridConfig = {}
        # Start checking queue for progress.
        if mode == 'determinate':
            # Once assigned variable, progressbar turns on 'determinate' progress_mode.
            self.widgets['Progress'].configure(variable=self.progress)
            self._watch()
        else:
            self._wait()

    def pack(self, *args, **kwargs):
        """Pack child widgets in a column."""
        self.widgets['Progress'].pack(side='left', fill='both', expand=False)
        self.widgets['Stage'].pack(side='right', fill='both', expand=False)
        super().pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        """
        Pack child widgets by find portions,
        and preserve grid config for restoring upon UI filtering.
        """
        self.grid_rowconfigure(0, weight=1)  # Layout single widgets.
        # Main widgets
        col = 0
        for k, v in self.widgets.items():  # Layout each column.
            self.grid_columnconfigure(col, weight=self.gridWeights[k])
            v.grid(row=0, column=col, sticky=FULL_EXPAND)
            col += 1
        super().grid(*args, **kwargs)
        self.gridConfig = kwargs

    def _watch(self):
        # Periodically check queue for messages from worker thread.
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                self.stage.set(msg[0])
                self.progress.set(msg[1])
            except self.queue.Empty:
                pass
        self.after(50, self._watch)

    def _wait(self):
        # Show indeterminate progress till the external process finishes
        # Start and stop on special queue messages.
        while self.queue.qsize():
            msg = self.queue.get(0)
            if msg[0] == '/start':
                self.widgets['Progress'].start()
            elif msg[0] == '/stop':
                self.widgets['Progress'].stop()
            else:
                raise NotImplementedError(
                    'Unexpected progress message: {}'.format(msg[0])
                )
            # return
        self.after(50, self._wait)


class SubmitStrip(tk.Frame):
    """
    A group of buttons as the submit step of form-submission workflow.
    It's stateless observer of the parameter widgets.
        - Submit: The main action of the form.
        - Cancel: Abort and save nothing.
        - Save As: Save all parameters as a preset JSON.
        - Load: Load a preset JSON and show on the parameter rack.
        - Save Default: Save all parameters to defaults.json.
        - Reset All: Reset all parameters to default.
    Handlers are implemented on app side,
    because whether to use config or args is a user decision.
    """

    def __init__(self, parent, targets, config_man, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=COLOR_LAYERS['Action'], padx=10, pady=5)
        # Data
        self.targets = targets  # Link to source widgets that we observe.
        self.config_man = config_man
        self.config = config_man.load()
        self.ext = '.json'
        self.filetypes = [('Config Files', '*.json')]
        self.basename = splitext(util.MAIN_CFG_FILENAME)[0] + '-preset'
        # Preset
        self.widgets = collections.OrderedDict()
        self.widgets['Self'] = self
        self.widgets['PresetFrame'] = tk.Frame(self,
                                               bg=COLOR_LAYERS['Action'],
                                               padx=10)
        self.widgets['SaveAs'] = ttk.Button(self.widgets['PresetFrame'],
                                            text='Save As',
                                            command=self._on_save_as)
        self.widgets['Load'] = ttk.Button(self.widgets['PresetFrame'],
                                          text='Load',
                                          command=self._on_load)
        self.widgets['SaveDefault'] = ttk.Button(self.widgets['PresetFrame'],
                                                 text='Save Default',
                                                 command=self._on_save_default)
        self.widgets['ResetAll'] = ttk.Button(self.widgets['PresetFrame'],
                                              text='Reset All',
                                              command=self._on_reset_all)
        self.widgets['Log'] = ttk.Button(self.widgets['PresetFrame'],
                                         text='Open Log',
                                         command=self._on_open_log)
        # Submit
        self.widgets['SubmitFrame'] = tk.Frame(self,
                                               bg=COLOR_LAYERS['Action'],
                                               padx=15)
        self.widgets['Submit'] = tk.Button(
            self.widgets['SubmitFrame'],
            text='Go!',
            command=self._on_submit,
            highlightbackground='#{:02X}{:02X}{:02X}'.format(10, 150, 100),
            highlightthickness=5
        )
        self.widgets['Cancel'] = ttk.Button(self.widgets['SubmitFrame'],
                                            text='Cancel',
                                            command=self._on_cancel)
        # Handlers: bind hooks to default implementation.
        self.handlers = {k: None for k in ['OnCancel',
                                           'OnSubmit']}

    def configure_internal(self, config):
        """
        Configure individual widgets.
        :param config: {wgtKey: {property: value, ...}, ...}
                        Refers to widget by widgets's key, then its property.
        :return:
        """
        for k, props in config.items():
            for p, v in props.items():
                self.widgets[k][p] = v

    def pack(self, *args, **kwargs):
        for key in ['SaveAs', 'Load', 'SaveDefault', 'ResetAll', 'Log']:
            self.widgets[key].pack(side='left', expand=False)
        for key in ['Submit', 'Cancel']:
            self.widgets[key].pack(side='right', expand=False)
        self.widgets['PresetFrame'].pack(side='left', fill='x', expand=False)
        self.widgets['SubmitFrame'].pack(side='right', fill='x', expand=False)
        super().pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        for key in ['SaveAs', 'Load', 'SaveDefault', 'ResetAll', 'Log']:
            self.widgets[key].pack(side='left', expand=False)
        for key in ['Submit', 'Cancel']:
            self.widgets[key].pack(side='right', expand=False)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.widgets['PresetFrame'].grid(row=0, column=0, sticky='news')
        self.widgets['SubmitFrame'].grid(row=0, column=1, sticky='news')
        super().grid(*args, **kwargs)

    def bind_internal(self, eventmaps):
        """
        Register events and handlers.
        Handlers can receive cookies from internal delegates.
        Input can be partial of total handler collection,
        so that 1+ handler classes can implement entire handlers collectively,
        based on their own data.
        :param eventmaps: {'OnXX": handlerFunc} for internal event delegate.
        :return:
        """
        for k, v in eventmaps.items():
            self.handlers[k] = v

    def _on_save_as(self):
        """
        Read widgets' states;
        Update config's 'Value' fields according to the states;
        Save config file via prompt.
        """
        self.config_man.update_widgets(self.targets)
        title = 'Save As Preset: '
        path = tkfiledialog.asksaveasfilename(
            title=title,
            defaultextension=self.ext,
            filetypes=self.filetypes,
            initialfile=self.basename
        )
        if path == '':  # Cancelled.
            return
        self.config_man.save_as(path)

    def _on_load(self):
        """
        Load config file via prompt;
        Update widgets' states.
        """
        title = 'Load Preset: '
        path = tkfiledialog.askopenfilename(
            title=title,
            defaultextension=self.ext,
            filetypes=self.filetypes,
            initialfile=self.basename
        )
        if path == '':  # Cancelled
            return
        self.config_man.load_from(path)
        self.config_man.update_widgets(self.targets)

    def _on_save_default(self):
        """
        Save current widgets' states to default config file after confirmation.
        """
        self.config_man.update_from_widgets(self.targets)
        if not tkmsgbox.askokcancel('Data Integrity',
                                    'Overwrite the default config file?'):
            return
        self.config_man.save_default()

    def _on_reset_all(self):
        """
        Load default config file and update widgets' states after confirmation.
        """
        if not tkmsgbox.askokcancel('Data Integrity',
                                    'Discard all edits and reset to default?'):
            return
        self.config_man.load_default()
        self.config_man.update_widgets(self.targets)

    def _on_open_log(self):
        """
        Open log in a webbrowser for better cross-platform behaviours.
        Heuristics
        - Log file is called <app_basename>.log under the app folder.
        :return:
        """
        log_url = pathlib.Path(join(self.config_man.app_dir, 'app.log')).as_uri()
        webbrowser.open(log_url)

    def _on_submit(self):
        """
        Save widget states into main config file in place.
        Delegate actual submit behaviour to app, e.g., which program to run.
        The runner can be a python function that calls an external program,
        e.g., shell script or .exeIt must use the config file.
        """
        self.config_man.update_from_widgets(self.targets)
        self.config_man.save()
        self.handlers['OnSubmit']()

    def _on_cancel(self):
        """
        Close window by default if no app handler is registered, otherwise run
        app handler instead, which may or may not close the window.
        """
        if not callable(self.handlers['OnCancel']):
            root = self.winfo_toplevel()
            if root is not None:
                root.destroy()
        else:
            self.handlers['OnCancel']()


class MultiOptionMenu(tk.Frame):
    def __init__(self, *args, text='Choose Multiple', **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(bg='purple')
        # Data
        self.choices = collections.OrderedDict()
        self.toSelectAll = tk.IntVar(name='All', value=1)
        self.toSelectNone = tk.IntVar(name='None', value=0)
        # widgets
        self.menubutton = ttk.Menubutton(self, text=text)
        self.menu = tk.Menu(self.menubutton, tearoff=False)
        self.menubutton.configure(menu=self.menu)
        self.menu.add_command(label='All',
                              command=self._select_all)
        self.menu.add_command(label='None',
                              command=self._select_none)

    def configure_internal(self, config):
        """Config: {'Title', ..., 'MultiOptions': [opt1, ...]}"""
        self.menubutton['text'] = config['Title']
        for choice in config['MultiOptions']:
            self.choices[choice] = tk.BooleanVar(name=choice, value=True)
            self.menu.add_checkbutton(label=choice,
                                      variable=self.choices[choice],
                                      onvalue=True,
                                      offvalue=False)

    def get_data(self):
        """Return the selected options."""
        return [k for k in filter(lambda k: self.choices[k].get() == 1,
                                  self.choices.keys())]

    def pack(self, *args, **kwargs):
        self.menubutton.pack(side='left', fill='x', expand=True)
        super().pack(*args, **kwargs)

    def _select_all(self):
        # Select all options.
        for k, v in self.choices.items():
            v.set(1)

    def _select_none(self):
        # Update all option menu items on All or None.
        for k, v in self.choices.items():
            v.set(0)


class SearchBar(tk.Frame):
    """
    Keyword-based search bar.
    Similar to Go-To-Anything bar of Sublime.
    Features
    - Search while typing in keywords;
    - Results reflect in the associated widgets, e.g., visible listbox item;
    - Search history of specified size, showing in dropdown list;
    - Search in specified domains, e.g., _name, tag, property.
    Usage
    - Configure to register 'OnChange' handler in parent class
      for search-while-typing.
    """
    def __init__(self, *args, **kwargs):
        """
        :param parent: parent widget
        :param name: top-level key in config
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.configure(bg=COLOR_LAYERS['Common'], padx=20)

        self.history = []
        self.defaultText = ''
        self.input = tk.StringVar(name=self._name, value=self.defaultText)
        self.handlers = {}

        self.widgets = collections.OrderedDict()
        self.gridWeights = {}
        self.handlers['OnSearch'] = None
        self.widgets['Scope'] = MultiOptionMenu(self, name='where', text='Where')
        self.widgets['Search'] = ttk.Combobox(self, textvariable=self.input)
        self.widgets['Reset'] = ttk.Button(self,
                                           text='Clear',
                                           command=self._on_reset)
        self.widgets['Search'].bind('<Button-1>', self._on_click_in)
        self.widgets['Search'].bind('<Leave>', self._on_leave)
        self.widgets['Search'].bind('<Return>', self._on_key_enter)

    def configure_internal(self, config):
        key = 'Scope'
        if key in config.keys():
            self.widgets[key].configure_internal(config[key])

    def grid(self, *args, **kwargs):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1000)
        self.grid_columnconfigure(2, weight=1)
        self.widgets['Scope'].grid(row=0, column=0, sticky='e')
        self.widgets['Search'].grid(row=0, column=1, sticky='e')
        self.widgets['Reset'].grid(row=0, column=2, sticky='w')
        super().grid(*args, **kwargs)

    def pack(self, *args, **kwargs):
        self.widgets['Scope'].pack(side='left', fill='x', expand=False)
        self.widgets['Search'].pack(side='left', fill='x', expand=True)
        self.widgets['Reset'].pack(side='left', fill='x', expand=False)
        super().pack(*args, **kwargs)

    def _on_click_in(self, evt):
        # Clear default text to get ready for user type-in.
        if self.widgets['Search'].get() == self.defaultText:
            evt.widget.delete(0, 'end')
            self.input.set('')

    def _on_leave(self, evt):
        """Restore default text to show it's a search bar."""
        if self.input.get() == '':
            self.widgets['Search'].set(self.defaultText)

    def _on_key_enter(self, evt):
        self.history.append(self.input.get())

    def _on_reset(self):
        self.input.set('')
        self.widgets['Search'].set(self.defaultText)

    def get_selected_domains(self):
        return [key for key, domain in self.widgets['Scope'].choices.items()
                if domain.get()]

    def bind_internal(self, eventmaps):
        """
        Register events and handlers. Handlers support internal cookies.
        :param eventmaps: {'OnXX": handlerFunc} for internal event delegate.
        :return:
        """
        for key in eventmaps.keys():
            self.handlers[key] = eventmaps[key]

        # Bind var observer: lambda to pass the var value to client.
        # CAUTION: passing widget as self to app.
        if callable(self.handlers['OnChange']):
            self.input.trace(
                mode='w',
                callback=lambda *args: self.handlers['OnChange'](self, *args)
            )


class SingleExplorer(tk.Frame):
    def __init__(self, parent, name, projdir, *args, **kwargs):
        super().__init__(parent, *args, name=name, **kwargs)
        self.widgets = collections.OrderedDict()
        self.widgets['Search'] = SearchBar(self, name='search')
        # self.widgets['Tree'] = ttk.Button(self,
        # name='tree', selectmode='extended')
        self.widgets['Tree'] = ttk.Button(self, name='tree')

    def grid(self, *args, **kwargs):
        self.grid_rowconfigure(0, weight=1)
        self.widgets['Search'].grid(row=0, column=0, sticky=FULL_EXPAND)
        self.grid_rowconfigure(1, weight=1)
        self.widgets['Tree'].grid(row=1, column=0, sticky=FULL_EXPAND)
        super().grid(*args, **kwargs)

    def pack(self, *args, **kwargs):
        self.widgets['Search'].pack(side='top', fill='x', expand=True)
        self.widgets['Tree'].pack(side='top', fill='both', expand=True)
        super().pack(*args, **kwargs)


class Explorer(tk.Frame):
    """
    Tabbed-treeview with separate hierarchy trees under each tab.
    Features
    - Construct tabbed-view based on project folder structure, folder => tab.
    - Each 2nd-level physical folder is a root node within a tree.
    - Search by keywords to narrow down;
    - Node = checkbox + icon + colour + name, expandable representation;
    - Multi-Edit;
    - Excluding nodes;
    - Color-coding through icon;
    - Side-by-side split view.
    """
    def __init__(self, parent, tabnames, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(padx=5, pady=5)
        # Widgets
        self.widgets = collections.OrderedDict()
        self.widgets['Search'] = SearchBar(self, name='search')
        self.widgets['Tabs'] = ttk.Notebook(self, name='tabs')
        for name in tabnames:
            tab = ttk.Frame(self.widgets['Tabs'])
            self.widgets['Tabs'].add(tab, text=name)
            monty = ttk.LabelFrame(tab, text=' Monty Python ')
            monty.grid(column=0, row=0, padx=8, pady=4)
        self.widgets['Tabs'].enable_traversal()

    def grid(self, *args, **kwargs):
        self.grid_rowconfigure(0, weight=1)
        self.widgets['Search'].grid(row=0, column=0, sticky=FULL_EXPAND)
        self.grid_rowconfigure(1, weight=1)
        self.widgets['Tabs'].grid(row=1, column=0, sticky=FULL_EXPAND)
        super().grid(*args, **kwargs)

    def pack(self, *args, **kwargs):
        self.widgets['Search'].pack(side='top', fill='x', expand=False)
        self.widgets['Tabs'].pack(side='top', fill='both', expand=True)
        super().pack(*args, **kwargs)


# =========================================================================
# Factories and Builders
# =========================================================================
def create_simple_root(title, size=None, resizable=(False, False), onquit=None):
    """Create a non-resizeable root window, and show it at the center screen."""
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

    # CAUTION: on macOS, Icon becomes the dock image.
    icon_file = join(_script_dir, 'icon.gif')
    if exists(icon_file):
        root.iconphoto(True, tk.PhotoImage(file=icon_file))

    root.clipboard_clear()
    root.attributes('-topmost', True)
    root.focus_force()
    root.bind('<FocusIn>', unpin_root_on_focus_in)

    def quit_app():
        if callable(onquit):
            onquit()
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', quit_app)
    root.bind('<Escape>', lambda e: quit_app())
    return root


class ParamUIBuilder:
    """
    Generate tkinter widgets for input config parameters,
    as a vertical rack of widget rows for each top-level field,
    based on config file.
    :param parent: parent frame that holds the parameter rack.
    :param config_man: config manager handling config file i/o.
    :param watchers: configs containing observers of parameter
    changes,
                           i.e., {'widgetKey': handler, ...}.
    """
    def __init__(self, parent, config_man, watchers=None):
        self.parent = parent
        self.config_man = config_man
        self.watchers = watchers

    def build(self):
        """
        Build parameter rack row by row.
        """
        config = self.config_man.load()
        row_idx = 0
        for k, v in config.items():
            widget_type = ParamUIBuilder._get_type(v)
            name = k.lower()
            if widget_type == 'bool':
                row = CheckStrip(self.parent, name=name)
            elif widget_type in ('int', 'float'):
                row = NumberStrip(self.parent, name=name, datatype=widget_type)
            elif widget_type == 'Info':
                row = InfoStrip(self.parent, name=name)
            elif widget_type == 'Label':
                row = TitleStrip(self.parent, name=name)
            elif widget_type == 'Option':
                row = OptionStrip(self.parent, name=name)
            elif widget_type == 'Path':
                row = PathStrip(self.parent, name=name)
            elif widget_type == 'Separator':
                row = Separator(self.parent, name=name)
            elif widget_type == 'Entry':
                row = EntryStrip(self.parent, name=name)
            else:
                raise RuntimeError(
                    'Unsupported widget type: {}'.format(widget_type)
                )
            row.configure_internal(v)
            if hasattr(row, 'input'):
                row.bind_internal({
                    'OnReset': self._on_reset_widget,
                    'OnHelp': self._on_widget_help
                })
                if self.watchers is not None and k in self.watchers.keys():
                    # {'Key': {'OnChange': handler}, ...}
                    row.bind_internal(self.watchers[k])
            self.parent.grid_rowconfigure(row_idx, weight=1)
            self.parent.grid_columnconfigure(0, weight=1)
            row.grid(row=row_idx, column=0, sticky=FULL_EXPAND)
            row_idx += 1

    @staticmethod
    def _get_type(field):
        # Retrieve primitive data type by decoding config field.
        # :param field: dict that satisfies
        #     - bool: {'Value': bool, ...}
        #     - number: {'Value': int/float, ...}
        #     - option: {'Value': [], 'Select': number, ...}
        #     - path: {key: value, ..., "Type": "Path", ...}
        #     - separator: {}
        #     - Label: {'Title': str} needs no input and thus has no value.
        #     - Info: {'Title': str, Content: str} multiline text, readonly.
        # :return: Widget type.
        # CAUTION: Tests below are order-sensitive!!
        if len(field.keys()) == 0:
            return 'Separator'
        if 'Value' not in field.keys():
            return 'Label'
        if isinstance(field['Value'], str):
            return field['Type'] if 'Type' in field.keys() else 'Entry'
        if 'Options' in field.keys():  # Must test before numbers.
            return 'Option'
        return type(field['Value']).__name__  # number and bool

    def _on_reset_widget(self, wgt_name):
        # Reset handler for all widgets to decouple the retrieval approaches,
        # e.g., read from file or some other way.
        default = self.config_man.load_default()
        return default[wgt_name]

    def _on_widget_help(self, wgt_name):
        default = self.config_man.load_default()
        return default[wgt_name]['Help']


def build_submit_ui(parent, targets, config_man,
                    on_submit=None, on_cancel=None):
    """
    Builder that builds the submit UI.
    It must be child of root window to be able to close it.
    :param parent: root window of the app.
    :param targets: widgets for the submit strip to observe.
    :param config_man: Config manager that handles i/o of config.
    :param on_submit: function for submitting a configured command.
    :param on_cancel: function for cancelling the submission
                       or stopping the running command.
    :return:
    """
    strip = SubmitStrip(parent,
                        targets,
                        config_man)
    strip.bind_internal({'OnSubmit': on_submit, 'OnCancel': on_cancel})
    return strip


def build_script_launcher(title, app_dir, progress_queue,
                          handlers={}, window_size=(768, 768),
                          progress_mode='determinate'):
    """
    Build common launcher for a multi-parameterized script.
    :param title: Window title.
    :param app_dir: App dir holding config files.
    :param progress_queue: Queue that stores progress messages for threads.
    :param handlers: Main handlers for submit, cancel, quit.
    :param window_size: Size of the root window.
    :param progress_mode: whether progressbar is determinate or not
    :return: root window.
    """
    root = create_simple_root(
        title,
        window_size,
        onquit=handlers['OnQuit'] if 'OnQuit' in handlers.keys() else None)

    search_bar = SearchBar(root, name='search')
    search_bar.configure_internal({
        'Scope': {
            'Title': 'Where',
            'MultiOptions': ['Name', 'Title', 'Help']
        }
    })
    search_bar.pack(side='top', fill='both', expand=False)

    mainframe = ScrollFrame(root)
    mainframe.pack(side='top', fill='both', expand=True)
    search_bar.bind_internal({
        'OnChange': lambda w, *args: mainframe.filter_widgets(
            w.input.get(),
            search_bar.get_selected_domains()
        )
    })

    # Generate param UI
    config_man = util.SingletonDecorator(ConfigMan)(app_dir)
    param_builder = ParamUIBuilder(mainframe.frame,
                                   config_man,
                                   watchers=handlers['Watchers']
                                   if 'Watchers' in handlers.keys() else None)
    param_builder.build()
    submit_strip = build_submit_ui(
        root,
        mainframe.frame.winfo_children(),
        config_man,
        # on_submit=functools.partial(main, argv=[sys.argv[0], '-c']),
        on_submit=handlers['OnSubmit']
        if 'OnSubmit' in handlers.keys() else None,
        on_cancel=handlers['OnCancel']
        if 'OnCancel' in handlers.keys() else None
    )
    submit_strip.configure_internal({'Cancel': {'text': 'Quit'}})
    submit_strip.pack(side='top', fill='both', expand=False)
    progress_bar = ProgressStrip(root, queue=progress_queue, mode=progress_mode)
    progress_bar.pack(side='top', fill='both', expand=False)
    return root


def test1():
    root = create_simple_root('kkGUI', (768, 768))

    explorer = Explorer(root, name='explorer',
                        tabnames=[d for d in
                                  os.listdir(join(_script_dir, 'test_explorer'))
                                  if not d.startswith('.')])
    explorer.pack(side='left', fill='both', expand=True)
    right_frm = tk.Frame(root, bg='green')
    search_bar = SearchBar(right_frm, name='searchprop')
    search_bar.configure_internal(
        {
            'Scope': {'Title': 'Where',
                      'MultiOptions': ['Name', 'Title', 'Help']
                      }
        }
    )
    search_bar.pack(side='top', fill='x', expand=False)
    prop_panel = ScrollFrame(right_frm)
    # If expand == False, you'll need to scroll no matter what;
    # fill='x' will make you scroll even more.
    prop_panel.pack(side='top', fill='both', expand=True)
    search_bar.bind_internal(
        {'OnChange': lambda w, *args: prop_panel.filter_widgets(
            w.input.get(), search_bar.get_selected_domains())
         }
    )
    right_frm.pack(side='right', fill='both', expand=True)

    i_row, delta = 0, 3
    for r in range(delta):
        row = EntryStrip(prop_panel.frame, name='interpreter')
        prop_panel.frame.grid_rowconfigure(i_row + r, weight=1)
        prop_panel.frame.grid_columnconfigure(0, weight=1)
        row.grid(row=i_row + r, column=0, sticky=FULL_EXPAND)
    i_row += delta

    for r in range(delta):
        row = NumberStrip(prop_panel.frame, name='age', datatype='int')
        prop_panel.frame.grid_rowconfigure(i_row + r, weight=1)
        prop_panel.frame.grid_columnconfigure(0, weight=1)
        row.grid(row=i_row + r, column=0, sticky=FULL_EXPAND)
    i_row += delta

    for r in range(delta):
        row = CheckStrip(prop_panel.frame, name='enablecheat')
        prop_panel.frame.grid_rowconfigure(i_row + r, weight=1)
        prop_panel.frame.grid_columnconfigure(0, weight=1)
        row.grid(row=i_row + r, column=0, sticky=FULL_EXPAND)
    i_row += delta

    for r in range(delta):
        row = OptionStrip(prop_panel.frame, name='fruits')
        options = ('Apple', 'Orange', 'Watermelon')
        row.configure_internal({'Value': 1,
                                'Title': 'Options: ',
                                'Options': options})
        prop_panel.frame.grid_rowconfigure(i_row + r, weight=1)
        prop_panel.frame.grid_columnconfigure(0, weight=1)
        row.grid(row=i_row + r, column=0, sticky=FULL_EXPAND)

    action_strip = SubmitStrip(
        root,
        prop_panel.frame.winfo_children(),
        config_man=util.SingletonDecorator(ConfigMan)(_script_dir)
    )
    action_strip.pack(side='top', fill='both', expand=False)
    root.mainloop()


def test2():
    root = create_simple_root('kkGUI', (768, 768))

    explorer = Explorer(root, name='explorer',
                        tabnames=[d for d in os.listdir(join(_script_dir,
                                                             'test_explorer'))
                                  if not d.startswith('.')])
    explorer.pack(side='left', fill='both', expand=True)

    root.mainloop()


if __name__ == '__main__':
    test1()
