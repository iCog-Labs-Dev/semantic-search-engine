import os
import pandas as pd
from src.util.config import *

def get_all_channels(path):
  df = pd.read_json(path + 'channels.json')

  channel_ids = [id for id in df['id']]
  channel_names = [ name for name in df['name']]

  return pd.DataFrame({ 'channel_id': channel_ids, 'channel_name': channel_names } )

channels = get_all_channels(slack_data_path)