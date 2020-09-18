from moviepy.editor import VideoFileClip, concatenate_videoclips
import os
import glob
import pandas as pd
import subprocess
import numpy as np


#1. concatentate all of the files
participant_dir = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/lindsay_pilot'
buffer_vid_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/video_cutter/white_2s.mp4'
output_video_path = "/Users/stephanmeylan/Downloads/lindsay_pilot.mp4"
output_metadata_path = "/Users/stephanmeylan/Downloads/lindsay_pilot.csv"
expected_number_of_trials = 36

def get_duration(filname):
	command = "ffprobe -i "+filname+" -show_format -v quiet | sed -n 's/duration=//p'"
	result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
	rval = float(result.stdout.decode('utf-8').replace('\n',''))
	return(rval)	

def match_video_audio_durations(filepath):
	command = 'ffmpeg -y -i '+filepath+' -map 0 -c copy -fflags +shortest -max_interleave_delta 0 '+filepath.replace('.mp4','_trimmed.mp4')
	print(command)
	subprocess.call(command.split(' '))

def concat_mp4s(input_video_paths, output_video_path):
	concat = ['ffmpeg','-y']#[paths.FFMPEG]
	inputList = ''

	# If there are no files to concat, immediately return 0.
	if not len(input_video_paths):
		return 0

	# Build the concatenate command	
	for (iVid, vid) in enumerate(input_video_paths):
		concat = concat + ['-i', str(vid)]
		inputList = inputList + '[{}:0][{}:1]'.format(iVid, iVid)		

	# Concatenate the videos
	concat = concat + ['-filter_complex', inputList + 'concat=n={}:v=1:a={}'.format(len(input_video_paths), 1) + '[out]',
		'-map', '[out]', output_video_path, '-loglevel', 'error', "-c:v", "libx264", "-preset", "slow",
		"-b:v", "1000k", "-maxrate", "1000k", "-bufsize", "2000k",
		"-c:a", "libfdk_aac", "-b:a", "128k"]
	print('Concat command:')
	print(' '.join(concat))

	subprocess.call(concat)



gazetracking_mp4s = [x for x in glob.glob(os.path.join(participant_dir, '*gazetracking*.mp4'))  if 'trimmed' not in x] 
# match video and audio duration first, before the concatenation
[match_video_audio_durations(x) for x in gazetracking_mp4s]

trimmed_gazetracking_mp4s = glob.glob(os.path.join(participant_dir, '*gazetracking*_trimmed.mp4'))

mp4_df = pd.DataFrame({"file" : trimmed_gazetracking_mp4s})
mp4_df['durations'] = [get_duration(x) for x in mp4_df.file]

if mp4_df.shape[0] != expected_number_of_trials:
	raise ValueError('Trial videos are missing. Expecting '+str(expected_number_of_trials) +' videos but found '+str(mp4_df.shape[0]))
else:
	print('Expected number of videos found ('+str(expected_number_of_trials)+')')

#total_duration_inputs = np.sum(mp4_df['durations'])
buffer_video = VideoFileClip(buffer_vid_path)
videos_to_code = [VideoFileClip(x) for x in mp4_df.file]
joined_files =  concatenate_videoclips(videos_to_code[0:5], method='compose', transition=buffer_video)
joined_files.write_videofile(output_video_path,  codec='libx264', audio=True, audio_codec='aac')

# do the actual concatenation
#concat_mp4s(mp4_df.file, output_video_path)


mp4_df['index'] = range(mp4_df.shape[0])
mp4_df['simple_end_time']  =   np.cumsum(mp4_df['durations'])
simple_start_times = [0] + mp4_df['simple_end_time'].tolist()
mp4_df['simple_start_time'] = simple_start_times[0:(len(simple_start_times) - 1)]
mp4_df['start_time'] = 2 * mp4_df['index'] + mp4_df['simple_start_time']
mp4_df['end_time'] = 2 * mp4_df['index'] + mp4_df['simple_end_time']
mp4_df.to_csv(output_metadata_path)



import pdb
pdb.set_trace() 

#[ ] add back the 
#[ ]  Better to 
#[ ] revisit the encoding to restore the waveforms (aac)
# issue with concatenating videos
	# -- try switching the codec
	# recall concatenating was a problem in ffmpeg (reason we switched to moviepy)


