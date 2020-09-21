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

def trim_video_audio_durations(filepath):
	command = 'ffmpeg -y -i '+filepath+' -map 0 -c copy -fflags +shortest -max_interleave_delta 0 '+filepath.replace('.mp4','_trimmed.mp4')
	print(command)
	subprocess.call(command.split(' '))

def buffer_video_audio_durations(filepath):
	#command = 'ffmpeg -y -i '+filepath+' -map 0 -c copy -fflags +shortest -max_interleave_delta 0 '+filepath.replace('.mp4','_buffered.mp4')
	command = 'ffmpeg -y -i '+filepath+' -map 0 -c copy -fflags +shortest -max_interleave_delta 0 '+filepath.replace('.mp4','_buffered.mp4')
	print(command)
	subprocess.call(command.split(' '))

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
			"-c:a", "libfdk_aac", "-b:a", "256k"]
		print('Concat command:')
		print(' '.join(concat_command))

		subprocess.call(concat_command)


	if method == 'chain':
		# generate 2s lead-in text videos for reference
		
		filenames = pd.DataFrame({'file':['file '+ x for x in input_video_paths]})
		filenames.to_csv('input.txt', header = False, index = False)
		concat_command = 'ffmpeg -y -f concat -safe 0 -i input.txt -c copy '+output_video_path
		subprocess.call(concat_command.split(' '))


gazetracking_mp4s = [x for x in glob.glob(os.path.join(participant_dir, '*gazetracking*.mp4'))  if 'trimmed' not in x] 
# match video and audio duration first, before the concatenation
#[trim_video_audio_durations(x) for x in gazetracking_mp4s]

#trimmed_gazetracking_mp4s = glob.glob(os.path.join(participant_dir, '*gazetracking*_trimmed.mp4'))

mp4_df = pd.DataFrame({"file" : gazetracking_mp4s})
mp4_df['durations'] = [get_duration(x) for x in mp4_df.file]

if mp4_df.shape[0] != expected_number_of_trials:
	raise ValueError('Trial videos are missing. Expecting '+str(expected_number_of_trials) +' videos but found '+str(mp4_df.shape[0]))
else:
	print('Expected number of videos found ('+str(expected_number_of_trials)+')')

#total_duration_inputs = np.sum(mp4_df['durations'])
#buffer_video = VideoFileClip(buffer_vid_path)
#videos_to_code = [VideoFileClip(x) for x in mp4_df.file]
#joined_files =  concatenate_videoclips(videos_to_code[0:5], method='compose', transition=buffer_video)
#joined_files.write_videofile(output_video_path,  codec='libx264', audio=True, audio_codec='aac')

# do the actual concatenation
concat_mp4s(mp4_df.file, output_video_path, 'reencode')

mp4_df['index'] = range(mp4_df.shape[0])
mp4_df['simple_end_time']  =   np.cumsum(mp4_df['durations'])
simple_start_times = [0] + mp4_df['simple_end_time'].tolist()
mp4_df['simple_start_time'] = simple_start_times[0:(len(simple_start_times) - 1)]
mp4_df['start_time'] = 2 * mp4_df['index'] + mp4_df['simple_start_time']
mp4_df['end_time'] = 2 * mp4_df['index'] + mp4_df['simple_end_time']
mp4_df.to_csv(output_metadata_path)


# [X] try re-encoding it by dropping -c copy -- check if this works, if not then comment back in -c copy in the command. It doesn't work
# https://stackoverflow.com/questions/13041061/mix-audio-video-of-different-lengths-with-ffmpeg
#[ ] add back the white transition video
#[ ] revisit the encoding to restore the waveforms (aac). Try switching the codec
# issue with concatenating videos -- only in Mike's? Or also in Lindsay	
	# Recall that there was a problem with audio-video timing matches in 

# Resulting file says that it has a duration of 569s and source duration of 571s
# summed video durations is 571.325
# summed (longer of video, audio) durations is 571.451
# so we could try audiopadding all of them? And allow for the drift
# if we trim them first, then we have a problem aligning it with the metadata

# extract audio from video
#ffmpeg -i input-video.avi -vn -acodec copy output-audio.aac
#https://stackoverflow.com/questions/9913032/how-can-i-extract-audio-from-video-with-ffmpeg

#ffmpeg -i videoStream_28d2d07e-92d7-45cb-b6d3-60dbfc910e2e_7-gazetracking-p4_d726312d-be7e-4839-b955-7a2c2bbf6ecf_1599020263224_181.mp4 -i videoStream_28d2d07e-92d7-45cb-b6d3-60dbfc910e2e_7-gazetracking-p4_d726312d-be7e-4839-b955-7a2c2bbf6ecf_1599020263224_181.aac -c:v copy -af apad -shortest test.mp4
# cuts it to the duration of the audio

#ffmpeg -i videoStream_28d2d07e-92d7-45cb-b6d3-60dbfc910e2e_7-gazetracking-p4_d726312d-be7e-4839-b955-7a2c2bbf6ecf_1599020263224_181.mp4 -i videoStream_28d2d07e-92d7-45cb-b6d3-60dbfc910e2e_7-gazetracking-p4_d726312d-be7e-4839-b955-7a2c2bbf6ecf_1599020263224_181.aac -filter_complex " [1:0]apad " -shortest test2.mp4
# cuts it to the duration of the audio

# run first
#ffmpeg -i videoStream_28d2d07e-92d7-45cb-b6d3-60dbfc910e2e_7-gazetracking-p4_d726312d-be7e-4839-b955-7a2c2bbf6ecf_1599020263224_181.mp4 -c copy -an videoStream_28d2d07e-92d7-45cb-b6d3-60dbfc910e2e_7-gazetracking-p4_d726312d-be7e-4839-b955-7a2c2bbf6ecf_1599020263224_181_noaudio.mp4
# this yields a video that is as long as the audio, again. This is probably indicative of the problem


#https://superuser.com/questions/801547/ffmpeg-add-audio-but-keep-video-length-the-same-not-shortest
