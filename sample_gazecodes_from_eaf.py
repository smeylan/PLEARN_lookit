import pympi
import pandas as pd
import numpy as np
import glob
import os
import argparse

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
    processed_frames_df = pd.DataFrame(processed_frames)
    if validate_frames(processed_frames_df)
        return(processed_frames_df)

def validate_frames(processed_frames_df):
    #!!! logic for validation requirements, allowable number of unlabled frames, goes here.
    return (True)

def read_eaf_to_table(eaf_path):
    '''Get a table representation of the default tier labels from an EAF'''
    annots = get_annots(eaf_path)
    frames = get_frame_ts_for_video(eaf_path.replace('.eaf','.mp4'))
    labels = get_label_for_frames(annots, frames)
    return(labels[['ms','label']])


def main(args): 
    print(args)
    import pdb
    pdb.set_trace()
    #!!! this is for one eaf file per video
    #filenames = glob.glob(os.path.join(data_path, "*.eaf"))
    
    if args.session is not None:
        filenames = glob.glob(os.path.join(args.data_basepath,'lookit_data', session, 'annotations','*.eaf'))        
    else:
        filenames = glob.glob(os.path.join(args.data_basepath,'lookit_data', '*', 'annotations','*.eaf'))

    if args.doublecode:
        filenames  = [x for x in filenames if 'doublecode' in x]
    else:
        filenames  = [x for x in filenames if 'doublecode' not in x]
    
    
    for eaf_file in filenames:
        # [ ] !!! read in in the  corresponding timing metadata
        # [ ] !!! read in the  correpsonding frame times


        df = read_eaf_to_table(eaf_file)
        df['filename'] = os.path.basename(eaf_file)
        
        if not args.validate: 
            df.to_csv(os.path.join(data_path, 'gaze_codes.csv'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sample labels for unique frames from an ELAN-tagged EAF file...')
    parser.add_argument('--data_basepath',
                           type=str,
                           action='store',
                           help='The data root for the project (should include lookit_data as a directory, containing folders corresponding to sessions) ')
    parser.add_argument('--session',                       
                           action='store',
                           type=str,
                           help='The session identifier under lookit-data to process. If unspecified, then all sessions in `lookit_data` will be processed.')
    parser.add_argument('--validate',                       
                           action='store_true',
                           help='If this is a validation run, run the checks but do not output a file for gaze codes')

    parser.add_argument('--doublecode',                       
                           action='store_true',
                           help='If sampling from an eaf doing double-coding, then include this flag so that the script checks for completion on double-coded trials only')
    args = parser.parse_args()


    main(args)