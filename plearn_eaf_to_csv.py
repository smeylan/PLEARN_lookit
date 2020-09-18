import pympi
import pandas as pd
import numpy as np
import glob
import os

data_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/jonah_pilot'
filenames = glob.glob(os.path.join(data_path, "*.eaf"))
print(filenames)

def get_annots(eaf_path): 
    '''Get annoations from the EAF '''
    print('Processing '+eaf_path)
    eaf = pympi.Elan.Eaf(eaf_path)
    annots = pd.DataFrame(eaf.tiers['default'][0].values())
    annots = annots.rename(columns = {0:'start_ms', 1: 'end_ms', 2:'label', 3:'drop'})
    annots = annots.drop(labels = 'drop', axis=1)
    validate_annots(annots.label)
    annots.start_ms = [eaf.timeslots[x] for x in annots.start_ms]
    annots.end_ms = [eaf.timeslots[x] for x in annots.end_ms]
    annots = annots.sort_values(by='start_ms')
    return(annots)

def validate_annots(labels):
    '''Confirm all codes are in the set of acceptable codes'''
    label_options = ('lost', 'frozen', 'away', 'eyes closed', 'left', 'right', 'center', 'no child')
    unknown_labels = set(labels) - set(label_options)
    if len(unknown_labels) > 0:
        raise ValueError('Unknown labels in annotation file: '+' '.join(unknown_labels))

def get_frame_ts_for_video(video_path):
    '''Get the timestamps for unique frames. These align with ELAN'''
    ts_path = video_path.replace('.mp4','.time')
    ffprobe_command = "ffprobe "+ video_path + " -select_streams v " \
    + "-show_entries frame=coded_picture_number,pkt_pts_time -of " \
    + "csv=p=0:nk=1 -v 0 > "+ts_path
    os.system(ffprobe_command)
    ts_table = pd.read_csv(ts_path, header=None)
    ts_table = ts_table.rename(columns = {0:'ms',1:'unk'})
    ts_table['ms'] = ts_table['ms'] * 1000
    # I thought unk was frame indices, but the numbers are all over
    return(ts_table[['ms']])

def get_label_for_frames(annots, frames):
    '''Get a label from annots for each frame in frames'''
    processed_frames = []
    for frame in frames.to_dict('records'):
        frame_annotations = annots.loc[(annots.start_ms <= frame['ms']) & \
            (annots.end_ms >= frame['ms'])]
        if frame_annotations.shape[0] == 1:
            frame['label'] = frame_annotations.iloc[0]['label']
        elif frame_annotations.shape[0] == 0:
            print('frame does not have a corresponding annotation: '+str(frame['ms']))
            frame['label'] = None
        elif frame_annotations.shape[0] > 1:
            print('frame has more than one corresponding annotation: '+str(frame['ms']))
            frame['label'] = None
        processed_frames.append(frame)
    return(pd.DataFrame(processed_frames))

def read_eaf_to_table(eaf_path):
    '''Get a table representation of the default tier labels from an EAF'''
    annots = get_annots(eaf_path)
    frames = get_frame_ts_for_video(eaf_path.replace('.eaf','.mp4'))
    labels = get_label_for_frames(annots, frames)
    return(labels[['ms','label']])


all_processed_eaf = []
for eaf_file in filenames:
    df = read_eaf_to_table(eaf_file)
    df['filename'] = os.path.basename(eaf_file)
    all_processed_eaf.append(df)
processed_df = pd.concat(all_processed_eaf)
processed_df.to_csv(os.path.join(data_path, 'gaze_codes.csv'))

# [ ]  Plearn_eaf should complain about durations of untagged video beyond a certain duration