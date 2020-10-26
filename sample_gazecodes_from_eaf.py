import pympi
import pandas as pd
import numpy as np
import glob
import os
import argparse
import math
import subprocess
import shutil

def get_annots(eaf_path, label_options): 
    '''Get annoations from the EAF '''
    print('Processing '+eaf_path)
    eaf = pympi.Elan.Eaf(eaf_path)
    annots = pd.DataFrame(eaf.tiers['default'][0].values())
    annots = annots.rename(columns = {0:'start_ms', 1: 'end_ms', 2:'label', 3:'drop'})
    annots = annots.drop(labels = 'drop', axis=1)    
    annots.start_ms = [eaf.timeslots[x] for x in annots.start_ms]    
    annots.end_ms = [eaf.timeslots[x] for x in annots.end_ms]
    annots['start_time'] = [translate_ms_to_mm_ss(x) for x in annots.start_ms]
    annots['end_time'] = [translate_ms_to_mm_ss(x) for x in annots.end_ms]
    annots = annots.sort_values(by='start_ms')
    annots.index = [x+1 for x in annots.index]
    validate_annots(annots, label_options)
    return(annots)

def validate_annots(annots, label_options):
    '''Confirm all codes are in the set of acceptable codes'''

    invalid_annots = annots.loc[~annots.label.isin(label_options)]

    if invalid_annots.shape[0] > 0:
        print('Invalid annotations found in the file')
        print(invalid_annots)
        raise ValueError('stopping because of bad annotations in label file. Fix the annotations above in the original EAF and try again')
    else:
        print('File passed label validation check!')
        return(annots)

def translate_ms_to_mm_ss(ms):
    '''translate a time in ms to a time mm:ss.dd which is easier to look up in ELAN or other video editing software'''
    s = ms / 1000
    r_m = int(math.floor(s / 60.))
    r_s = s - (r_m * 60.)

    return(str(r_m).zfill(2)+':'+str(int(r_s)).zfill(2)+'.'+str(round(r_s - int(r_s), 3)).replace('0.',''))

def get_labels_for_frames(annots, frames, trial_times):
    '''Get a label from annots for each frame in frames, and associate with a trial'''

    processed_frames = []
    for frame in frames.to_dict('records'):

        trial = trial_times.loc[(trial_times.start_time_ms <= frame['ms']) & \
            (trial_times.end_time_ms >= frame['ms'])]
        if trial.shape[0] == 0:
            frame['label'] = 'interstitial'
            frame['type'] = 'transition video'
            frame['trial'] = None
            processed_frames.append(frame)
        else:
            # get a trial identifier from the trial times for each frame
            frame['trial'] = os.path.basename(trial.iloc[0].file).split('_')[2]

            frame_annotations = annots.loc[(annots.start_ms <= frame['ms']) & \
                (annots.end_ms > frame['ms'])] #if a frame falls on an annotation boundary, it gets grouped with the interval that starts at that time
            if frame_annotations.shape[0] == 1:
                frame['label'] = frame_annotations.iloc[0]['label']
                frame['type'] = 'participant video'
            elif frame_annotations.shape[0] == 0:
                print('frame does not have a corresponding annotation: '+translate_ms_to_mm_ss(frame['ms']))
                frame['label'] = 'missing'
                frame['type'] = 'participant video'
            elif frame_annotations.shape[0] > 1:
                print('frame has more than one corresponding annotation: '+translate_ms_to_mm_ss(frame['ms']))
                frame['label'] = 'multiple'
                frame['type'] = 'participant video'
            processed_frames.append(frame)
    processed_frames_df = pd.DataFrame(processed_frames)
    if validate_frames(processed_frames_df):
        return(processed_frames_df)

def validate_frames(processed_frames_df):
    '''check if a sufficient number of frames have been labeled'''
    #could also check if frames follow requirements for transitions (i.e. transition frames must be between left and right labeled frames)
    participant_videos = processed_frames_df.loc[(processed_frames_df.type == 'participant video')]
    no_missing_data = participant_videos.loc[participant_videos.label != 'missing']
    proportion_complete = no_missing_data.shape[0] / float(participant_videos.shape[0])
    print("Proportion of frames labeled: "+str(round(proportion_complete, 4)))
    if proportion_complete < .98:
        raise ValueError('Insufficient proportion of frames have been labeled. At least 98% of frames must be labeled to pass validation.')
    else:
        print('File has a sufficient number of frames labeled!')
        return (True)

def get_frame_ts_for_video(time_path):
    '''load the file with timestamps for unique frames'''
    frames = pd.read_csv(time_path)
    frames.columns = ['ms', 'original_frame_index'] # why is this out of order
    frames['frame_index'] = range(1, frames.shape[0]+1) # this should match with the frame-by-frame output
    return(frames)

def process_eaf(eaf_path, session_id, label_options, args):
    '''Get a table representation of the default tier labels from an EAF'''
    annots = get_annots(eaf_path, label_options)
    
    time_paths = glob.glob(os.path.join(os.path.dirname(eaf_path),'*.time'))
    if len(time_paths) > 1:
        raise ValueError('More than one time file found at '+basepath(eaf_path))
    else:
        frames = get_frame_ts_for_video(time_paths[0])

    trial_times_paths = glob.glob(os.path.join(os.path.dirname(eaf_path),'*'+session_id+'*.csv')) # need a way to capture this w/o the output csv
    trial_times_paths = [x for x in trial_times_paths if '_' not in os.path.basename(x)] # underscore in output csv but not the originial timing csv
    trial_times = pd.read_csv(trial_times_paths[0])
    trial_times['start_time_ms']= trial_times.start_time * 1000
    trial_times['end_time_ms']= trial_times.end_time * 1000
    trial_times['trial'] = [os.path.basename(x).split('_')[2] for x in trial_times.file]


    # get a label for each frame
    labels = get_labels_for_frames(annots, frames, trial_times)

    if args.validate:
        return(labels)
    else:
        # adjust the time if not validate
        # adjust the times so that 0 is stimulus onset in each case
        frame_event_data_original_path = glob.glob(os.path.join(str(os.path.dirname(eaf_path)).replace('lookit_data/'+session_id+'/processed', 'lookit_frame_data'), '*'+session_id+'_frames.csv'))
        if len(frame_event_data_original_path) > 1:
            print(frame_event_data_original_path)
            raise ValueError('More than one frame event found for '+session_id)
        elif len(frame_event_data_original_path) == 0:
            raise ValueError('No frame event data found for '+session_id)
        else:
            frame_event_data_original_path = frame_event_data_original_path[0]

        lookit_frame_filename = os.path.basename(frame_event_data_original_path)
        frame_event_new_path = os.path.join(str(os.path.dirname(eaf_path)).replace('processed','frame_events'), session_id+'_frames.csv')
        shutil.copy(frame_event_data_original_path, frame_event_new_path)

        shutil.copy(frame_event_data_original_path, frame_event_new_path)    
        frame_events = read_frame_events(frame_event_new_path)

        time_normalized_labels = normalize_label_times(labels, trial_times, frame_events)
        return(time_normalized_labels)

def splitDFByCols(df, cols):
    '''split a dataframe into dataframes addressable by key cols'''
    gb = df.groupby(cols)   
    rdict = {}
    for group in gb.groups:
        rdict[group] = gb.get_group(group)
    return(rdict)

def read_frame_events(frame_events_path):
    
    raw_frame_events = pd.read_csv(frame_events_path)
    raw_frame_events = raw_frame_events.loc[~np.isnan(raw_frame_events.event_number)]

    #convert to short form from long -- associate everything with the same frame id
    # Want a line for each frameId + eventType
    timing_data_short = raw_frame_events.pivot(index=['frame_id', 'event_number'], columns= ['key'], values='value').reset_index()

    

    # do a second pivot so we have the timestamp of each event type
    frame_event_timings = timing_data_short.pivot_table(index=['frame_id'], columns= 'eventType', values='timestamp', aggfunc='first').reset_index()

    # need to cast the timestamps into times with as.posix or something
    time_cols = list(set(frame_event_timings.columns) - set(['frame_id']))

    for time_col in time_cols:
        frame_event_timings[time_col] = pd.to_datetime(frame_event_timings[time_col])

    seconds_recording_before_stim = (frame_event_timings['exp-lookit-video:videoStarted'] - frame_event_timings['exp-lookit-video:startRecording'])

    frame_event_timings['seconds_recording_before_stim'] = [x.total_seconds() for x in seconds_recording_before_stim]
   
   # expect these to be positive values. If values are negative, it means that the kids are seeinig some of the video before recording begins

    # check if any of these are negative
    if any(frame_event_timings['seconds_recording_before_stim']  < 0):
        raise ValueError('Stims start before recording, violating assumptions.')

    #tds_by_event = splitDFByCols(timing_data_short, ['frame_id'])
    return(frame_event_timings)

def normalize_label_times(labels, trial_times, frame_events):
    '''get the start time for all trials and compute the time in ms with respect to video start (not stimulus onset, which requires the actual stimuli timings; this is done in the analysis stack)'''
    
    # first, normalize so that the start of each video is 0, using the trial start times in trial_times
    labels_with_start_time = labels.merge(trial_times[['trial','start_time_ms']], how='left')
    if (labels_with_start_time.shape[0] != labels.shape[0]):
        raise ValueError('Some video frames (stills) could not be associated with trial metadata.')
    labels_with_start_time['normalized_ms'] = round(labels_with_start_time['ms'] - labels_with_start_time['start_time_ms'])
    
    # second, normalize so that 0 is the stimulus onset, using the timings in the frame_events
    labels_with_video_start_time = labels_with_start_time.merge(frame_events[['frame_id', 'seconds_recording_before_stim']], left_on='trial', right_on='frame_id') 
    
    labels_with_video_start_time['normalized_ms'] = labels_with_video_start_time['normalized_ms'] - 1000 *(labels_with_video_start_time['seconds_recording_before_stim'])
    
    return(labels_with_video_start_time)


def extract_stills_for_frames(eaf_file, regenerate):
    annotator_id  = os.path.basename(eaf_file).split('_')[0] # in case I want to use the annotator ID
    mp4_path = os.path.join(os.path.dirname(eaf_file), os.path.basename(eaf_file).split('_')[1].replace('.eaf','.mp4'))
    output_dir = str(os.path.dirname(mp4_path)).replace('processed', 'video_frames/temp')
    output_path = os.path.join(output_dir, '%04d.jpg')

    
    left_dir = str(os.path.dirname(mp4_path)).replace('processed', 'video_frames/left')
    if len(glob.glob(left_dir) )> 1 and not regenerate:
        print('Skipping generation of stills...')
    else:
        print('Extracting stills...')
        # extract all stills to temp
        extract_stills_command = 'ffmpeg -i '+mp4_path+' -qscale:v 2 '+output_path
        print(extract_stills_command)
        subprocess.call(extract_stills_command.split(' '))
    
    # sort the files into the appropriate directories
    labels = pd.read_csv(eaf_file.replace('.eaf','.csv')) 
    for frame in labels.to_dict('records'):
        src_path = os.path.join(output_dir, str(frame['frame_index']).zfill(4)+'.jpg')
        destination_path = os.path.join(str(output_dir).replace('video_frames/temp', 'video_frames'), frame['label'], str(frame['frame_index']).zfill(4)+'.jpg') 
        shutil.move(src_path, destination_path)
    
    # get the annotator and the video path from the eaf file
    # delete temp directory
    shutil.rmtree(output_dir)

    print('Extracted stills successfully!')

def main(args):     

    if args.validate and args.extract_stills:
        raise ValueError('Stills cannot be extracted during a validation check. Remove either --validate or --extract_stills')
    if args.doublecode:
         raise NotImplementedError
    if args.session is None:
        if args.validate:
            print('Validating all EAF transcriptions in'+os.path.join(args.data_basepath,'lookit_data'))            
        else:  
            print('Processing all EAF transcriptions in'+os.path.join(args.data_basepath,'lookit_data'))

        filenames = glob.glob(os.path.join(args.data_basepath,'lookit_data',  '*','processed','*.eaf'))        
        raise NotImplementedError("Need to think about how to retrieve all of the session_ids")


    else:
        filenames = glob.glob(os.path.join(args.data_basepath,'lookit_data',  args.session,'processed','*.eaf'))        
        if args.validate:
            print('Validating EAF transcriptions:')           
        else:
            print('Processing EAF transcriptions:')
        print(filenames)

    for dir in ['video_frames', 'frame_events']:
        dir_to_create = os.path.join(args.data_basepath, 'lookit_data', args.session, dir)
        if not os.path.exists(dir_to_create):
            os.makedirs(dir_to_create)

    # make directories in which to place the labeled frames
    label_options = ('lost', 'frozen', 'away', 'eyes closed', 'left', 'right', 'center', 'no child', 'transition') 
    for dir in list(label_options) + ['temp', 'interstitial','missing','multiple']: #temp is where ffmpeg will write stuff; interstitial is for the inter-video labels
        dir_to_create = os.path.join(args.data_basepath, 'lookit_data', args.session, 'video_frames', dir)
        if not os.path.exists(dir_to_create):
            os.makedirs(dir_to_create)

    for eaf_file in filenames:
        df = process_eaf(eaf_file, args.session, label_options, args)
        
        if not args.validate:
            df.to_csv(eaf_file.replace('.eaf','.csv'), index=False) # formerly gaze_codes.csv
            print("Gaze codes .csv written to "+eaf_file.replace('.eaf','.csv'))
        else:
            print("Validation flag is set, not writing gaze code file...")

        # get an image for every timeslice, put it in "frames"
        if args.extract_stills:
            extract_stills_for_frames(eaf_file, regenerate=False)

    print('Success! Annotations successfully parsed for session '+args.session)

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
    parser.add_argument('--extract_stills',                       
                           action='store_true',
                           help='Extract JPGs for each labeled frame for review')
    parser.add_argument('--doublecode',                       
                           action='store_true',
                           help='If sampling from an eaf doing double-coding, then include this flag so that the script checks for completion on double-coded trials only')
    args = parser.parse_args()


    main(args)