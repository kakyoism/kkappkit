import collections
from os.path import abspath, dirname, join
import sys

import matplotlib

# Must stay right after import matplotlib to avoid backend errors.
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, \
    NavigationToolbar2Tk as NavigationToolbar
from matplotlib.ticker import FuncFormatter
import numpy as np
from scipy.io import wavfile

from ci.gui import kkgui as ui

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


_script_dir = abspath(dirname(__file__))


class FigureTrack(tk.Frame):
    def __init__(self, parent, name, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._name = name
        self.widgets = collections.OrderedDict()
        self.fig = plt.Figure()
        # Title bar
        self.vars = collections.OrderedDict()
        self.vars['ToHide'] = tk.BooleanVar(value=False)
        self.widgets['TitleBar'] = tk.Frame(self, bg='red')
        self.widgets['Title'] = ttk.Label(self.widgets['TitleBar'], text='Title')
        self.widgets['Hide'] = ttk.Checkbutton(self.widgets['TitleBar'],
                                               text='Hide',
                                               variable=self.vars['ToHide'],
                                               command=self._on_hide)
        # Track
        self.widgets['TrackFrame'] = tk.Frame(self, bg='green')
        fig_widget = FigureCanvasTkAgg(self.fig,
                                       master=self.widgets['TrackFrame'])
        self.widgets['Track'] = fig_widget.get_tk_widget()
        # Toolbar
        self.widgets['ToolFrame'] = tk.Frame(self, bg='purple')
        self.widgets['Toolbar'] = NavigationToolbar(fig_widget,
                                                    self.widgets['ToolFrame'])
        self.gridConfig = {
            'TitleBar': {'row': 0, 'column': 0, 'sticky': ui.FULL_EXPAND},
            'TrackFrame': {'row': 1, 'column': 0, 'sticky': ui.FULL_EXPAND},
            'ToolFrame': {'row': 2, 'column': 0, 'sticky': ui.FULL_EXPAND},
        }
        # Debug
        self.configure(bg='blue')

        # Handlers
        self.handlers = {'OnDraw': None}

    def configure_internal(self, config):
        pass

    def grid(self, *args, **kwargs):
        # Title bar
        self.widgets['TitleBar'].grid_rowconfigure(0, weight=1)
        self.widgets['TitleBar'].grid_columnconfigure(0, weight=1)
        self.widgets['Title'].grid_columnconfigure(0, weight=1000)
        self.widgets['Title'].grid(row=0, column=0, sticky=ui.FULL_EXPAND)
        self.widgets['Hide'].grid_columnconfigure(1, weight=1)
        self.widgets['Hide'].grid(row=0, column=1, sticky='w')
        # Track
        self.widgets['Track'].grid_columnconfigure(0, weight=1)
        self.widgets['Track'].grid(row=0, column=0, sticky=ui.FULL_EXPAND)
        # Toolbar
        self.widgets['Toolbar'].grid_columnconfigure(0, weight=1)
        self.widgets['Toolbar'].grid(row=0, column=0, sticky=ui.FULL_EXPAND)

        for k in ['TitleBar', 'TrackFrame', 'ToolFrame']:
            self.widgets[k].grid(row=self.gridConfig[k]['row'],
                                 column=self.gridConfig[k]['column'],
                                 sticky=self.gridConfig[k]['sticky'])

        super().grid(*args, **kwargs)
        self.draw()

    def bind_internal(self, eventmaps):
        for key in eventmaps.keys():
            self.handlers[key] = eventmaps[key]

    def draw(self):
        self.handlers['OnDraw'](self.fig)

    def _on_hide(self):
        keys_to_hide = ['TrackFrame', 'ToolFrame']
        if self.vars['ToHide'].get():
            for k in keys_to_hide:
                self.widgets[k].grid_forget()
        else:
            for k in keys_to_hide:
                self.widgets[k].grid(row=self.gridConfig[k]['row'],
                                     column=self.gridConfig[k]['column'],
                                     sticky=self.gridConfig[k]['sticky'])


class AudioPlotter:
    """Import config and draw graphs as subplots"""
    def __init__(self, srcFile, config):
        self.srcFile = srcFile
        self.SR, self.signal = wavfile.read(self.srcFile)
        self.config = config
        # self.drawers = [GetDrawer() for ]

    def draw_audio_graph(self, fig):

        # plots = self.config['Plots']
        # nPlots = len(plots)
        # for p, plot in enumerate(plots):
        # 	ax = fig.add_subplot(nPlots, 1, p)
        # 	ax.set_title(plot['Title'])
        # 	ax.set_xlabel(plot['XLabel'])
        # 	ax.set_ylabel(plot['YLabel'])

        times = np.linspace(0,
                            self.signal.shape[0],
                            self.signal.shape[0]) / self.SR

        ax = fig.add_subplot(211)
        ax.set_title('Waveform')
        ax.set_xlabel('Time (Seconds)', horizontalalignment='right', x=1.0)
        ax.set_ylabel('Amplitude')
        ax.set_ylim(-1, 1)
        ax.set_yticks(np.arange(-1, 1), 0.1)

        if self.config['Scale'] == 'dB':
            def fmt(x, pos=None):
                """x = [-1, 1] for audio"""
                s = np.where(x != 0, 20 * np.log10(np.sign(x)*x), -np.inf)
                return '{:.1f}'.format(s)
            ax.yaxis.set_major_formatter(FuncFormatter(fmt))
        ax.plot(times, self.signal)

        ax = fig.add_subplot(212)
        ax.set_title('Spectrogram')
        ax.set_xlabel('Time (Seconds)', horizontalalignment='right', x=1.0)
        ax.set_ylabel('Frequency (Hz)')
        ax.set_ylim(0, self.SR/2)
        ax.specgram(self.signal, Fs=self.SR)

        # Space out subplots.
        fig.subplots_adjust(hspace=0.5)
        # fig.autofmt_xdate()

        plt.show()


if __name__ == '__main__':
    root = ui.create_simple_root('test', (656, 768), (True, False))
    mainFrame = ui.ScrollFrame(root)
    mainFrame.pack(side='top', fill='both', expand=True)

    mainFrame.frame.grid_rowconfigure(0, weight=1)
    mainFrame.frame.grid_columnconfigure(0, weight=1)
    track = FigureTrack(mainFrame.frame, 'Track1')
    plotter = AudioPlotter(join(_script_dir, 'y.wav'), {'Scale': 'dB'})
    track.bind_internal({'OnDraw': plotter.draw_audio_graph})
    track.grid(row=0, column=0, sticky=ui.FULL_EXPAND)

    root.mainloop()


