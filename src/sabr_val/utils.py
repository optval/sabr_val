import os
import datetime
import socket
import logging
import multiprocessing
from importlib import import_module

import matplotlib.pyplot as plt
import numpy as np
import yaml
import petname
import argparse, json, re
from datetime import datetime, timedelta
from time import mktime
import pandas as pd



def split_number_chars(s):
    res = re.split('([-+]?\d+\.\d+)|([-+]?\d+)', s.strip())
    res_f = [r.strip() for r in res if r is not None and r.strip() != '']
    return res_f


def to_year_fraction(s):
    s = s.lower()
    my_list = split_number_chars(s)
    n = len(my_list)
    if(n!=2):
        raise Exception(f"Invalid # of elements. Expected 2 found {n}")
        
    term = int(my_list[0])
    x = my_list[1][0]
    
    fraction = {'y' : 1.0, 'm' : 1.0/12.0, 'w' : 7.0/360.0, 'd' : 1.0/360.0}
    
    if x in list(fraction.keys()):
        term*= fraction[x]
    else:
        Exception(f"Uknow fraction type {x}")
    
    return term


def to_strike_shift(s):
    s = s.lower()
    my_list = split_number_chars(s)
    n = len(my_list)

    shift = 0.0
    x = ' '
    if(n==1 and my_list[0] == 'atm'):
        shift = 0.0
        x = 'atm'
    elif (n==2):
        shift = int(my_list[0])
        x = my_list[1]
    else:
        raise Exception(f"Invalid # of elements. Expected 2 found {n}")
        

    fraction = {'bps' : 1.0/10000, 'atm' : 0.01, ' ' : 1.0, 'rel' : 0.01}
    
    if x in list(fraction.keys()):
        shift*= fraction[x]
    else:
        Exception(f"Uknow fraction type {x}")
    
    return shift

def term_tenor_conversion(term_tenor_pair):
    term = [] 
    tenor = []
    for t in term_tenor_pair:
        t1, t2 = t.lower().split(' x ')
        term.append(to_year_fraction(t1))
        tenor.append(to_year_fraction(t2))

    return term, tenor




def parsing_date(text):
    text = str(text)
    if(len(text.split(' '))==3):
        t,t2,t3 = text.split(' ')
        text = t + ' ' + t2
        
    date_formats =['%Y%m%d','%Y/%m/%d','%Y-%m-%d','%Y%m%d %H:%M:%S.%f','%Y%m%d %H:%M:%S','%Y%m%d-%H:%M:%S','%Y%m%d-%H:%M:%S.%f','%Y%m%d%H:%M:%S','%Y%m%d%H:%M:%S.%f','%Y/%m/%d %H:%M:%S.%f','%Y/%m/%d %H:%M:%S','%Y/%m/%d-%H:%M:%S','%Y/%m/%d-%H:%M:%S.%f','%Y/%m/%d%H:%M:%S','%Y/%m/%d%H:%M:%S.%f','%Y-%m-%d %H:%M:%S.%f','%Y-%m-%d %H:%M:%S','%Y-%m-%d-%H:%M:%S','%Y-%m-%d-%H:%M:%S.%f','%Y-%m-%d%H:%M:%S','%Y-%m-%d%H:%M:%S.%f']

    for fmt in date_formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')


def parsing_datetime(col):    
    date_formats  =['%Y%m%d','%Y/%m/%d','%Y-%m-%d','%Y%m%d %H:%M:%S.%f','%Y%m%d %H:%M:%S','%Y%m%d-%H:%M:%S','%Y%m%d-%H:%M:%S.%f','%Y%m%d%H:%M:%S','%Y%m%d%H:%M:%S.%f','%Y/%m/%d %H:%M:%S.%f','%Y/%m/%d %H:%M:%S','%Y/%m/%d-%H:%M:%S','%Y/%m/%d-%H:%M:%S.%f','%Y/%m/%d%H:%M:%S','%Y/%m/%d%H:%M:%S.%f','%Y-%m-%d %H:%M:%S.%f','%Y-%m-%d %H:%M:%S','%Y-%m-%d-%H:%M:%S','%Y-%m-%d-%H:%M:%S.%f','%Y-%m-%d%H:%M:%S','%Y-%m-%d%H:%M:%S.%f']

    for fmt in date_formats :
        try:
            col = pd.to_datetime(col, errors="ignore", format= f"{fmt}")
        except ValueError:
            pass
    col = pd.to_datetime(col, errors="coerce") # To remove errors in the columns like strings or numbers
    return col



def str2bool(v)-> bool:
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    

def parse_list(s):
    return list(map(str,s.split(',')))

def parse_list_int(s):
    return list(map(int,s.split(',')))

def parse_list_tuples(s):
    list_pairs = parse_list(s)
    lst_tuples = [tuple(map(int, sub.split(' '))) for sub in list_pairs]
    return lst_tuples

def parse_list_tuples_int_str(s):
    list_pairs = parse_list(s)
    lst_tuples = [(int(sub.split(' ')[0]),str(sub.split(' ')[1])) for sub in list_pairs]
    return lst_tuples


def load_data_series(file_location, start_date, end_date, sep=',') :
    
    df = pd.read_csv(file_location,sep=sep)
    df['date'] = df['date'].astype(str)
    df.sort_values(by=['date'], inplace=True)
    df.drop_duplicates(['date'], keep='last', inplace=True)
    df.date = df.date.apply(parsing_date)
    df.reset_index(drop=True, inplace=True)

    # get validation trades above start date
    r_index  = (df.date >= start_date) & (df.date <= end_date) 
    df = df.loc[r_index]
    df.reset_index(drop=True,inplace=True)
    df.set_index('date',inplace=True)

    cols = df.columns.to_list()

    if ('volume' in cols):
        df['volume'][df.volume < 0] = 0
    if ('wap' in cols):
        df['wap'][df.wap < 0] = 0
    if ('barCount' in cols):
        df['barCount'][df.barCount < 0] = 0

    return df



def initialize_logging(app_name, logdir="logs", debug=False, run_id=None):
    debugtag = "-debug" if debug else ""
    logtag = petname.Generate(2)
    username = os.path.split(os.path.expanduser("~"))[-1]
    hostname = socket.gethostname().replace(".stanford.edu","")
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    starttimestr = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    if run_id is not None:
        raise Exception("Unimplemented")
        run_id = str(run_id)
        fh = logging.FileHandler(f"{logdir}/{app_name}{debugtag}_{run_id}_{logtag}_{username}_{hostname}_{starttimestr}.log")
        ch = logging.StreamHandler()
        # create formatter and add it to the handlers
        formatter = logging.Formatter(f"[%(asctime)s] Run{run_id} - %(levelname)s - %(message)s", '%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logging.getLogger('').handlers = []
        logging.getLogger('').addHandler(fh)
        logging.getLogger('').addHandler(ch)
        logging.info(f"HANDLER LEN: {len(logging.getLogger('').handlers)}")
        logging.getLogger('').level = logging.INFO if not debug else logging.DEBUG
    else:
        logging.basicConfig(
            level=logging.INFO if not debug else logging.DEBUG,
            format="[%(asctime)s] %(levelname)s - %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(f"{logdir}/{app_name}{debugtag}_{logtag}_{username}_{hostname}_{starttimestr}.log"),
                logging.StreamHandler()
            ]
        )
    logging.info(f"Logging initialized for '{app_name}' by '{username}' on host '{hostname}' with ID '{logtag}'")
    return username, hostname, logtag, starttimestr


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    From https://docs.djangoproject.com/en/dev/_modules/django/utils/module_loading/.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        ) from err

