from zipfile import ZipFile
import json
import os
import shelve

# each function needs to open and close the shelve file
# d = shelve.open('shelve')

def shelve_open_decorator(func):
    def wrapper(*args, **kwargs):

        if kwargs.get("d"):
            d = kwargs.pop("d")
            r = func(*args, d = d, **kwargs)
        else:
            with shelve.open("shelve") as d:
                r = func(*args, d = d, **kwargs)       
        
        return r
        
    return wrapper


def extract_zip(file : str) -> None:
    """extract from a zip file this will be used to easily upload export 
    data and be able to process it

    Parameters
    ----------
    file : any
        the zip file to open
    """
    with ZipFile(file, 'r') as zObject:
        zObject.extractall(path="temp")


@shelve_open_decorator
def users(d : shelve.Shelf | None = None):
    """read users important info from users is extracted ans saved to shelve
    """
    with open(os.getcwd() + '/temp/slack-export-data/users.json') as json_file:
        res = json.load(json_file) 
    users = []
    for user in res:
        u = {}
        # more items can be added here but these are the important ones for now
        u['id'] = user['id']
        u['name'] = user['name']
        u['is_bot'] = user['is_bot']
        u['real_name'] = user['profile']['real_name']
        u['avatar'] = user['profile']['image_192']
        u['email'] = user['profile']['email']
        # saving in shelve
        d[u['id']] = u
        users.append(u['id'])
    # saving a list of user id for later access
    d['users'] = users


@shelve_open_decorator
def channels(d : shelve.Shelf | None = None):
    """read channels, same thing with users but for channels
    """
    with open(os.getcwd() + '/temp/slack-export-data/channels.json') as json_file:
        info = json_file
        res = json.load(info)
    channels = []
    for channel in res:
        c = {}
        c['id'] = channel['id']
        c['name'] = channel['name']
        c['members'] = channel['members']
        c['purpose'] = channel['purpose']
        # this is arbitrary for now as we don't have  private channels exported here but later this should change
        c['type'] = 'public'
        d[c['id']] = c
        channels.append(c['id'])
    # list of channels for later reference
    d['channels'] = channels


@shelve_open_decorator
def channel_messages(channel_id :str, json_obj : [dict], d : shelve.Shelf | None = None):
    """reads messages from a single channel file.

    Parameters
    ----------
    channel_id : str
        the channel id of the channel where the messages belong
    json_obj : [dict]
        a list containing messages of the channel

    Returns
    -------
    [dict]
        extracted list of messages from a single channel file
    """
    messages = []
    for message in json_obj:
        # subtype == channel_join is a system message that tells a users has joined a channel, not really necessary
        if not ('subtype' in message and message['subtype'] == 'channel_join'):
            m = {}
            # more stuff can be extracted here but these are the essentials
            m['text'] = message['text']
            m['user'] = message['user']
            m['time'] = message['ts']
            m['channel'] = channel_id
            m['visibility'] = d[channel_id]['type']
            messages.append(m)
    return messages


@shelve_open_decorator
def channel_dir(channel_id : str, d : shelve.Shelf | None = None) -> [list]:
    """extracts all the messages from all channel files

    Parameters
    ----------
    channel_id : str
        the id of the specific channel

    Returns
    -------
    [list]
        a list of all messages from a single channel
    """
    # channels are their own folders in the export data
    directory = os.getcwd() + '/temp/slack-export-data/' + \
        d[channel_id]['name']
    # read all the files in that directory...this is assuming that all files in channel folders are json files
    files = os.listdir(directory)
    messages = []
    for file in files:
        with open(directory + '/' + file) as json_file:
            info = json.load(json_file)
        res = channel_messages(channel_id, info, d = d)
        # we concat the messages from a single json file 
        messages += res
    return messages

@shelve_open_decorator
def all_channels(d : shelve.Shelf | None = None):
    """
    extracts all messages from all the available channels
    Returns
    -------
    [dict]
        all the messages
    """
    all_messages = []
    for channel_id in d['channels']:
        # this is assuming that we need messages in a single list but this is open to change
        all_messages += channel_dir(channel_id, d = d)
    return all_messages