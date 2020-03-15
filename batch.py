# -*- cofing: utf-8 -*-

import os
from datetime import datetime as DT
import glob
from Incubator import Incubator, iprint

RAW_DIR = './raw'
JPG_DIR = './jpg'

if not os.path.exists(JPG_DIR):
    os.mkdir(JPG_DIR)

raw_files = list(map(lambda f: os.path.join(RAW_DIR, f), os.listdir(RAW_DIR)))
total_n = len(raw_files)

for count,raw_path in enumerate(raw_files):
    iprint('[{} - {:03d}/{:d}] Processing {}'.format(DT.now().strftime('%Y/%m/%d %H:%M:%S'), count+1, total_n, raw_path), 0)

    inc = Incubator()
    inc.open_raw(raw_path)
    inc.prepare()

    datetime = DT.strptime(inc.get_datetime(), '%Y:%m:%d %H:%M:%S\x00')
    date = datetime.strftime('%Y_%m_%d')
    filename_base = datetime.strftime('%Y%m%d_%H%M%S')

    # Create a directory with taken date
    if not os.path.exists(os.path.join(JPG_DIR, date)):
        os.mkdir(os.path.join(JPG_DIR, date))

    # When multiple files have the same datetime
    same_datetime_files = glob.glob(os.path.join(JPG_DIR, date, filename_base) + '*')
    base_path = os.path.join(JPG_DIR, date, filename_base)
    if same_datetime_files:
        jpg_path = base_path + '_{:02d}'.format(len(same_datetime_files)+1) + '.jpg'
    else:
        jpg_path = base_path + '.jpg'

    inc.make_loosy_jpg()
    inc.save_jpg(jpg_path)
