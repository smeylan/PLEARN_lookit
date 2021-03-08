import os
import subprocess as sp
import sys
import glob
import json
from moviepy.editor import VideoFileClip, concatenate_videoclips

# Order 1
# inputfile_path = '/Volumes/Seagate/Stephan/plearn_experiments/plearn_agreement1_whitebg.mp4' # the raw OBS recording of the experiment
# cutfile_path = "cut3.json" # the json specifying the times to cut
# output_path = "/Volumes/Seagate/Stephan/plearn_experiments/plearn_agreement1_whitebg_output" # where to put the result files

# Order 2
inputfile_path = "/Users/stephan/Movies/2021-02-26_18-34-50.mkv"
cutfile_path = "order2_cut.json"
output_path = "/Users/stephan/Dropbox (MIT)/Documents/MIT/research/PLEARN/order2/plearn_agreement2_whitebg_output"

regen_basefiles = True # regenerate the chopped files before converting to 4 formats for LookIt

def time_to_float(timestr):
	parts = timestr.split(':')
	if len(parts) != 3:
		raise ValueError('Time spec should be in format minutes:seconds:partial seconds (out of 60)')	
	total = float(parts[0])*60 + float(parts[1])+ float(parts[2]) / 100.
	return(total)


def fractional_time_to_decimal_time(fractional_time):
	parts = fractional_time.split(':')	
	if len(parts) != 3:
		print('parts')
		print(parts)
		raise ValueError('Time spec should be in format minutes:seconds:partial seconds (out of 60)')
	rstring = '00:'+str(parts[0])+':'+str(int(parts[1])+(float(parts[2]) / 100.)) 	
	return(rstring)

with open(cutfile_path, 'r') as f:
	trials = json.load(f) 

print('trials')
print(trials)

if regen_basefiles:
	for trial in trials:

		if trial['type'] == 'practice':

			# practice trial inter-trial time depends on key presses, so start and stop times have to be defined for each trial

			trial_output_path =  os.path.join(output_path, 'basetrial_'+ trial['filename_base']+'.mp4')
			
			command_list = ['ffmpeg', '-ss',str(trial['start_time']), '-to', str(trial['stop_time']), '-i', inputfile_path, '-ss', '0', '-y' , trial_output_path]
				#'-c', 'copy', '-avoid_negative_ts', 'make_zero',
				# the order of these is really critical; especially that the first ss seeks to the appropriate location and then the second resets the keyframe
			print('command to be called in subprocess')
			print(' '.join(command_list))
			sp.call(command_list)

		elif trial['type'] == 'test':		

			start_time = trial['start_time']
			end_time = start_time + trial['trial_duration']
			# Test trials are the same duration, so it's possible to specify the start time, the trial duration, and the pre-trial (gray screen) duration, as well as the number of trials

			for trial_index in range(1,trial['num_trials']+1):
			
				filename_base = str(trial_index)

				trial_output_path =  os.path.join(output_path, 'basetrial_'+ filename_base+'.mp4')

				command_list = ['ffmpeg', '-ss',str(start_time), '-to', str(end_time), '-i', inputfile_path, '-ss', '0', '-y' , trial_output_path]
				#'-c', 'copy', '-avoid_negative_ts', 'make_zero',
				# the order of these is really critical; especially that the first ss seeks to the appropriate location and then the second resets the keyframe
				print('command to be called in subprocess')
				print(' '.join(command_list))
				sp.call(command_list)

				start_time = end_time + trial['pretrial_duration']

				# increment by the pre-trial duration
				end_time = start_time +  trial['trial_duration']

video_files = glob.glob(
	os.path.join(output_path, "basetrial_*.mp4"))


for extension in ['mp4','mp4_nobuffer','webm']:
	media_path = os.path.join(output_path, extension)
	if not os.path.exists(media_path):
		os.makedirs(media_path)


for video_file in video_files:
	# get the base path
	video_base_path = os.path.dirname(video_file)
	video_name = os.path.basename(video_file).replace('basetrial_','')	

	# get the final element of the base path
	print(video_base_path)
	print(video_name)

	# make an mp4
	converted_file_output_path = os.path.join(video_base_path, 'mp4_nobuffer', video_name)
	command_list = ['ffmpeg', '-y', '-i', video_file, '-ss', '0', '-vf', 'scale=1280:-1', converted_file_output_path]
	print('command to be called in subprocess')
	print(' '.join(command_list))
	sp.call(command_list)
	# might need a -t duration

	
	white_2s = VideoFileClip("white_2s.mp4")
	content = VideoFileClip(converted_file_output_path)
	combined_files = concatenate_videoclips([white_2s,content])
	buffered_file_output_path = os.path.join(video_base_path, 'mp4', video_name)
	combined_files.write_videofile(buffered_file_output_path,  codec='libx264', audio=True, audio_codec='aac')

	# if os.path.exists('input.mp4'):	
	# 	sp.call('rm input.mp4', shell=True)	
	# sp.call('ln -s '+converted_file_output_path+ ' '+'input.mp4', shell=True)
	
	
	# vid_file_list = 'vid_file_list.txt'		
	# if os.path.exists(vid_file_list):
	# 	sp.call('rm '+vid_file_list, shell = True)	
	
	# sp.call('echo file  >'+vid_file_list, shell=True) 
	# sp.call('echo file input.mp4 >>'+vid_file_list, shell=True) 
	
	# # concatenate the white buffer mp4	
		
	# command_list = ['ffmpeg', '-y', '-f', 'concat', '-i', vid_file_list, buffered_file_output_path]
	# print('command to be called in subprocess')
	# print(' '.join(command_list))
	# sp.call(command_list)
	# # might need a -t duration


	# make a webm
	converted_file_output_path = os.path.join(video_base_path, 'webm', video_name.replace('mp4','webm'))
	command_list = ['ffmpeg', '-y', '-i', buffered_file_output_path,  '-ss', '0', '-c:v', 'libvpx', '-b:v', '4000k', '-maxrate', '4000k', '-bufsize','2000k', '-speed', '2', '-vf', 'scale=1280:-1', converted_file_output_path]
	print('command to be called in subprocess')
	print(' '.join(command_list))
	sp.call(command_list)

	# No longer making a separte webm file
	# make an mp3
	# converted_file_output_path = os.path.join(video_base_path, 'mp3', video_name.replace('mp4','mp3'))
	# command_list = ['ffmpeg', '-y', '-i', video_file,    '-ss', '0', '-vn', '-af', 'loudnorm=I=-16', converted_file_output_path]
	# print('command to be called in subprocess')
	# print(' '.join(command_list))
	# sp.call(command_list)

	# make an ogg
	# converted_file_output_path = os.path.join(video_base_path, 'ogg', video_name.replace('mp4','ogg'))
	# command_list = ['ffmpeg', '-y', '-i', video_file,    '-ss', '0', '-vn', '-af', 'loudnorm=I=-16', converted_file_output_path]
	# print('command to be called in subprocess')
	# print(' '.join(command_list))
	# sp.call(command_list)