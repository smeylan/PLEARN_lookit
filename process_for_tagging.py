from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os
import glob
import pandas as pd
import subprocess
import numpy as np
import argparse

def get_duration(filname):
	command = "ffprobe -i "+filname+" -show_format -v quiet | sed -n 's/duration=//p'"
	result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
	rval = float(result.stdout.decode('utf-8').replace('\n',''))
	return(rval)	

def trim_video_audio_durations(filepath):
	command = 'ffmpeg -y -i '+filepath+' -map 0 -c copy -fflags +shortest -max_interleave_delta 0 '+filepath.replace('.mp4','_trimmed.mp4')
	print(command)
	subprocess.call(command.split(' '))

def buffer_video_audio_durations(filepath):
	#command = 'ffmpeg -y -i '+filepath+' -map 0 -c copy -fflags +shortest -max_interleave_delta 0 '+filepath.replace('.mp4','_buffered.mp4')
	command = 'ffmpeg -y -i '+filepath+' -map 0 -c copy -fflags +shortest -max_interleave_delta 0 '+filepath.replace('.mp4','_buffered.mp4')
	print(command)
	subprocess.call(command.split(' '))

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
    ts_table.to_csv(ts_path, index=False)
    # I thought unk was frame indices, but the numbers are all over
    return(ts_table)

def concat_mp4s(input_video_paths, output_video_path, method):
	
	if method == 'reencode':
		concat_command = ['ffmpeg','-y']#[paths.FFMPEG]
		inputList = ''

		# If there are no files to concat, immediately return 0.
		if not len(input_video_paths):
			return 0

		# Build the concatenate command	
		for (iVid, vid) in enumerate(input_video_paths):
			concat_command = concat_command + ['-i', str(vid)]
			inputList = inputList + '[{}:0][{}:1]'.format(iVid, iVid)		

		# Concatenate the videos
		concat_command = concat_command + ['-filter_complex', inputList + 'concat=n={}:v=1:a={}'.format(len(input_video_paths), 1) + '[out]',
			'-map', '[out]', output_video_path, '-loglevel', 'error', "-c:v", "libx264", "-preset", "fast",
			"-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "3000k",
			"-f", "s16le", "-acodec",  "pcm_s16le", "-b:a", "256k"]
			#"-c:a", "libfdk_aac", "-b:a", "256k"]

		print('Concat command:')
		print(' '.join(concat_command))
		subprocess.call(concat_command)


	if method == 'chain':
		# generate 2s lead-in text videos for reference
		
		filenames = pd.DataFrame({'file':['file '+ x for x in input_video_paths]})
		filenames.to_csv('input.txt', header = False, index = False)
		concat_command = 'ffmpeg -y -f concat -safe 0 -i input.txt -c copy '+output_video_path
		subprocess.call(concat_command.split(' '))

def make_transition_clip(transition_bg_mov_path, txt, duration, screensize, output_path, regenerate):
	
	if os.path.exists(output_path) and regenerate == False:
		return(output_path)
	else:
		transition_bg_mov = VideoFileClip(transition_bg_mov_path)
		transition_bg_mov = transition_bg_mov.set_duration(duration)

		txtClip = TextClip(txt,color='black', font="Helvetica",
	                   kerning = 5, fontsize=40)
		txtClip = txtClip.set_duration(duration)

		cvc = CompositeVideoClip( [transition_bg_mov, txtClip.set_pos('center')], size=screensize)

		cvc.write_videofile(output_path)
		return(output_path)


def process_session(data_basepath, session, trim_videos = False, expected_number_of_trials = 45, encoding_method = 'reencode'):

	processed_dir = os.path.join(data_basepath, 'lookit_data', session, 'processed')
	if not os.path.exists(processed_dir):
		os.makedirs(processed_dir)
	
	gazetracking_mp4s = [x for x in glob.glob(os.path.join(data_basepath, 'lookit_data', session, 'raw','*gazetracking*.mp4'))  if 'trimmed' not in x] 

	# match video and audio duration before concatenating
	if trim_videos:
		[trim_video_audio_durations(x) for x in gazetracking_mp4s]
		gazetracking_mp4s = [x for x in glob.glob(os.path.join(data_basepath, 'lookit_data', session, 'raw','*gazetracking*.mp4'))  if 'trimmed' in x] 

	mp4_df = pd.DataFrame({"file" : gazetracking_mp4s})
	mp4_df['duration'] = [get_duration(x) for x in mp4_df.file]
	mp4_df['type'] = 'participant_recording'

	if mp4_df.shape[0] != expected_number_of_trials:
		raise ValueError('Trial videos are missing. Expecting '+str(expected_number_of_trials) +' videos but found '+str(mp4_df.shape[0]))
	else:
		print('Expected number of videos found ('+str(expected_number_of_trials)+')')

	
	# make the transition clips
	# get the properties of a single video
	example_video = VideoFileClip(mp4_df.file[0])

	transitions_dir = os.path.join(data_basepath, 'lookit_data', session, 'transitions')
	if not os.path.exists(transitions_dir):
		os.makedirs(transitions_dir)

	transition_clips = [] 
	for i in range(len(mp4_df.file)):
		transition_clips.append(make_transition_clip(transition_bg_mov_path= '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/video_cutter/white_2s.mp4', txt=os.path.basename(mp4_df.file[i]).replace('_','_\n'), duration =2, screensize = example_video.size, output_path= os.path.join(transitions_dir,str(i)+'.mp4'),
			regenerate = False)) 

	transitions_df = pd.DataFrame({"file" : transition_clips})
	transitions_df['duration'] = [get_duration(x) for x in transitions_df.file]
	transitions_df['type'] = 'transition_video'

	#intersperse the transition clips and the real clips
	transition_records = transitions_df.to_dict('records')
	participant_recording_records = mp4_df.to_dict('records') 
	if len(participant_recording_records) != len(transition_records):
		raise ValueError('There should be an equal number of participant recordings as transition videos')

	combined = []
	for i in range(len(participant_recording_records)):
		combined.append(transition_records[i])
		combined.append(participant_recording_records[i])

	combined_df = pd.DataFrame(combined)
	combined_df['end_time']  =   np.cumsum(combined_df['duration'])
	start_times = [0] + combined_df['end_time'].tolist()
	combined_df['start_time'] = start_times[0:(len(start_times) - 1)]

	participant_videos_df = combined_df.loc[combined_df.type == 'participant_recording']
	participant_videos_df['index'] = range(participant_videos_df.shape[0])

	# do the actual concatenation
	output_video_path = os.path.join(data_basepath, 'lookit_data', session, 'processed', session+'.mp4')	
	#concat_mp4s(combined_df.file, output_video_path, encoding_method)
	
	# write out the metadata
	output_metadata_path = os.path.join(data_basepath, 'lookit_data', session, 'processed', session+'.csv')
	participant_videos_df.to_csv(output_metadata_path)

	# get the unique frame timestamps
	get_frame_ts_for_video(output_video_path)

	print('Time difference: '+str(round(abs(get_duration(output_video_path) - participant_videos_df.tail(1).iloc[0].end_time), 3))+' seconds')
	
	participant_videos_df.tail(1).end_time


	# timing integrity checks
	#total_duration_inputs = np.sum(mp4_df['durations'])
	#buffer_video = VideoFileClip(buffer_vid_path)
	#videos_to_code = [VideoFileClip(x) for x in mp4_df.file]
	#joined_files =  concatenate_videoclips(videos_to_code[0:5], method='compose', transition=buffer_video)
	#joined_files.write_videofile(output_video_path,  codec='libx264', audio=True, audio_codec='aac')

def main(args):

	if args.session:
		session_dirs = [os.path.join(args.data_basepath, 'lookit_data', args.session)]
		sessions = [args.session]
	else:
		session_dirs = os.listdir(os.path.join(args.data_basepath, 'lookit_data'))
		sessions = [basepath(x) for x in session_dirs]

	[process_session(args.data_basepath, session) for session in sessions]



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
    args = parser.parse_args()
    main(args)