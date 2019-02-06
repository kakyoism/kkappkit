#!/usr/bin/env python

"""
Test app of kkGUI. Embed text into an image.

Dependencies: pip install pillow

Features
- CLI and GUI modes depending on whether user gives command options;
- Vertical parameter rack using factory methods parsing JSON configs;
"""

# Import built-in modules.
import functools
import logging
from os.path import abspath, basename, dirname, exists, join, split, splitext
import platform
from queue import Queue
import sys

# Import 3rd-party modules.
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw


# Metadata
__author__ = "Beinan Li"
__copyright__ = "Copyright $year$, Beinan Li"
__credits__ = ["Beinan Li"]
__license__ = "MIT"
__maintainer__ = "Beinan Li"
__email__ = "li.beinan@gmail.com"
__version__ = "0.3.2"


#
# Globals
#
_basename = splitext(basename(__file__))[0]
_script_dir = abspath(dirname(__file__))

sys.path.append(dirname(_script_dir))
# Import project modules.
import kkgui as ui
import util


_progress_queue = Queue()


def main(argv):
    """
    The app that does the job. Can also delegate to other (non-python) programs.
    :param argv: input commandline arguments
    :return:
    """
    logger = util.build_logger(__file__)
    # Silence logs from dependencies.
    logging.getLogger('PIL').setLevel(logging.ERROR)
    prompt = ui.Prompt(logger, is_gui=util.is_gui_mode(sys.argv))

    # Progress to update at the beginning of each stage.
    progress = (
        ('Load parameters ...', 1),
        ('Load image.', 10),
        ('Prepare text.', 30),
        ('Draw text on image.', 80),
        ('Save image.', 80),
        ('Success.', 100)
    )

    stage = 0
    _progress_queue.put(progress[stage])

    app_info = {
        'Script': __file__,
        'Task': 'Draw text on an input image file.',
        'Version': __version__
    }
    args = util.parse_args_config(argv, app_info)
    config = util.load_json(args.cfg_file)  # arg is a list under CLI.

    #
    # Retrieve parameters from config
    #
    # Example:
    #
    # fontname = u'/Library/Fonts/Songti.ttc'
    # fontsize = 100
    # inImg = join(_script_dir, 'images', 'test.png')
    # outImg = join(expanduser('~/Desktop/text.png'))
    # text = u'天呐!'
    # textpos = (50, 600)  # PIL allows to draw OUTSIDE of the image, must fix.
    # might see nothing.
    # color = (255,255,0)
    # color2 = '#aa0000'
    # toSaveCopy = False

    stage += 1
    _progress_queue.put(progress[stage])

    in_img = config['in_image']['Value']
    out_img = config['out_image']['Value']
    if not exists(in_img):
        if(not prompt.error(
                desc='Failed to find input image: {}'.format(in_img),
                causes=['File path is wrong.',
                        'File is renamed.',
                        'File is no longer there.'],
                suggestions=['Make sure the image path exists.',
                             'Check if something is touching file on the fly.'],
                confirm=True)):
            _progress_queue.put(progress[0])  # Reset progress at any bail!
            return 1
    im1 = Image.open(in_img).convert('RGBA')  # Open file to get size.

    stage += 1
    _progress_queue.put(progress[stage])

    font_name = config['font']['Options'][config['font']['Value']]
    fonts = {
        'Mac': {
            u'宋体': '/Library/Fonts/Songti.ttc',
            u'黑体': '/System/Library/Fonts/STHeiti Medium.ttc',
            u'Default': '/System/Library/Fonts/HelveticaNeue.ttc'
        },
        'Windows': {
            u'宋体': 'C:\\Windows\\Fonts\\SimSun.ttf',
            u'黑体': 'C:\\Windows\\Fonts\\SimHei.ttf',
            u'Default': 'C:\\Windows\\Fonts\\Verdana.ttf'
        }
    }
    plat = 'Mac' if platform.system() == 'Darwin' else 'Windows'
    font_path = fonts[plat][font_name]
    font_size = config['font_size']['Value']

    width, height = im1.size
    text = config['text']['Value']
    text_pos = (int(width * config['text_pos_x']['Value']),
                int(height * config['text_pos_y']['Value']))
    color = (config['color_r']['Value'],
             config['color_g']['Value'],
             config['color_b']['Value'])

    to_save_copy = config['save_copy']['Value']
    logger.info("""
    Parameters:
    ===========
    - Input Image: {}
    - Output Image: {}
    - Text: {}
    - Text pos: {}
    - Text colour: {}
    - Font: {}, Path: {}
    - Font size: {}
    - Save as a Copy: {}
""".format(in_img, out_img, text, text_pos, color, font_name, font_path,
           font_size, to_save_copy))

    if text_pos[0] > width or text_pos[1] > height:
        logger.error("""
    Text will be drawn outside of the image: 
    Expected: X < {}, Y < {}
    Got: {}
""".format(width, height, text_pos))

    #
    # Task: Draw the text on the picture
    #
    stage += 1
    _progress_queue.put(progress[stage])

    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(im1)
    draw.text(text_pos, text, fill=color, font=font)

    stage += 1
    _progress_queue.put(progress[stage])

    # Save the image copy with a new _name
    if to_save_copy:
        folder = split(in_img)[0]
        ext = splitext(in_img)[1]
        out_img = join(folder, _basename + '-copy-1' + ext)
        idx = 1
        while exists(out_img):
            idx += 1
            out_img = join(folder, _basename + '-copy-{}{}'.format(idx, ext))
    im1.save(out_img)

    stage += 1
    _progress_queue.put(progress[stage])
    logger.info('DONE.')
    return 0


def run_gui():
    """Run under GUI and non-verbose mode."""
    root = ui.build_script_launcher(
        title=_basename,
        app_dir=_script_dir,
        progress_queue=_progress_queue,
        handlers={
            'OnQuit': None,
            'OnSubmit': functools.partial(util.threaded_main, target=main),
            'OnCancel': None
        },
        window_size=(768, 768)
    )
    root.mainloop()


if __name__ == '__main__':
    if util.is_cli_mode(sys.argv):
        sys.exit(main(sys.argv))
    else:
        run_gui()
