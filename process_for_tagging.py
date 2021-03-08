from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os
import glob
import pandas as pd
import subprocess
import numpy as np
import argparse
import tempfile
import warnings

# usage python3 process_for_tagging.py --data_basepath ~/dropbox/Documents/MIT/research/PLEARN/lookit_data --session 4a038470-3533-4c2c-80bb-77fb2f6ed333 --buffervideo ~/dropbox/Documents/MIT/research/PLEARN/video_cutter/white_2s.mp4

def change_fps(input_filename, fps, regenerate = False):	
	output_filename = input_filename.replace('/raw/','/fps_matched/')	
	if os.path.exists(output_filename) and  regenerate == False:
		print('Not regenerating '+output_filename)
	else:
		fps_command = ['ffmpeg', '-y', '-i', input_filename, '-filter:v', 'fps='+str(fps), '-max_muxing_queue_size', '9999', "-c:a", "pcm_s32le", output_filename.replace('.mp4','.mkv')]
		print(' '.join(fps_command))
		subprocess.call(fps_command)

def get_duration(filename, method):
	'''get the duration to 3 decimal seconds for the filename'''
	# not sure what the difference in times between ffmprobe and mediainfo are
	if method == 'ffprobe':
		command = "ffprobe -i "+filename+" -show_format -v quiet | sed -n 's/duration=//p'"
		result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
		rval = float(result.stdout.decode('utf-8').replace('\n',''))
		return(rval)	
	elif method in ('mediainfo-video', 'mediainfo-audio'):
		
		if method == 'mediainfo-video':
			duration_command = 'mediainfo --Inform="Video;%Duration/String3%" ' + "-of default=noprint_wrappers=1:nokey=1 " + filename    
		else: 
			duration_command = 'mediainfo --Inform="Audio;%Duration/String3%" ' + "-of default=noprint_wrappers=1:nokey=1 " +  filename

		result = subprocess.run(duration_command, stdout=subprocess.PIPE, shell=True)
		mi_str = result.stdout.decode('utf-8').replace('\n','')
		video_components = mi_str.split(':')
		hours = video_components[0]
		minutes = video_components[1]
		seconds = video_components[2]    
		if hours == '00':
			hours = '0'
		if minutes == '00':
			minutes = '0' 
		mediainfo_video_duration = ((float(hours) * 60 * 60) + (float(minutes) * 60) + float(seconds))
		return(mediainfo_video_duration)		
	else:
		raise ValueError('Method must be one of mediainfo or ffprobe')

def trim_video_audio_durations(input_filename, regenerate):
	'''cut audio or video to the shortest of the two'''
	output_filename = input_filename.replace('/fps_matched/','/trimmed/')	
	if os.path.exists(output_filename) and  regenerate == False:
		print('Not re-triimming '+output_filename)
	else:
		#command = 'ffmpeg -y -i '+input_filename+' -map 0 -c copy -fflags +shortest -max_interleave_delta 0 '+output_filename
		
		# this should take cut audio to video length, and pad audio to match video otherwise		
		command = 'ffmpeg -y -i '+input_filename+' -c:v copy -af apad -shortest '+output_filename				
		print(command)
		subprocess.call(command.split(' '))

def get_frame_ts_for_video(video_path):
	'''Get the timestamps for unique frames'''
	root, extension = os.path.splitext(video_path)
	ts_path = video_path.replace(extension,'.time')
	ffprobe_command = "ffprobe "+ video_path + " -select_streams v " \
	+ "-show_entries frame=coded_picture_number,pkt_pts_time -of " \
	+ "csv=p=0:nk=1 -v 0 > "+ts_path
	os.system(ffprobe_command)
	ts_table = pd.read_csv(ts_path, header=None)
	ts_table = ts_table.rename(columns = {0:'ms',1:'unk'})
	ts_table['ms'] = ts_table['ms'] * 1000
	ts_table.to_csv(ts_path, index=False)
	return(ts_table)

def concat_mp4s(input_video_paths, output_video_path, method, fps=None):	

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
			'-map', '[out]', output_video_path.replace('.mp4','.mkv'), '-loglevel', 'error', "-c:v", "libx264", 
			"-c:a", "wav", "-b:a", "512k", "-f", "s32le", "-acodec",  "pcm_s32le", "-y"]

		# no audio for testing duration
		# concat_command = concat_command + ['-filter_complex', inputList + 'concat=n={}:v=1:a={}'.format(len(input_video_paths), 1) + '[out]',
		# 	'-map', '[out]', output_video_path, '-loglevel', 'error', "-c:v", "libx264", "-preset", "fast",
		# 	"-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "3000k", "-an"]
		#"-b:a", "256k", "-f", "s16le", "-acodec",  "pcm_s16le"]
		#"-c:a", "libfdk_aac", "-b:a", "256k"]

		print('Concat command:')		
		print(' '.join(concat_command))
		subprocess.call(concat_command)
		print('Finished mkv concatentation')

		# then convert the mkv to mp4 
		mkv_to_mp4_command = 'ffmpeg -i '+output_video_path.replace('.mp4','.mkv')+ ' -filter:v fps='+str(fps)+' -r '+str(fps)+' -y '+ output_video_path
		print('Converting mkv to mp4...')
		print(mkv_to_mp4_command)
		subprocess.call(mkv_to_mp4_command.split(' '))


	if method == 'chain':

		raise NotImplementedError # results in timing issues
		
		filenames = pd.DataFrame({'file':["file '"+ x+"'" for x in input_video_paths]})
		filenames.to_csv('input.txt', header = False, index = False)
		concat_command = 'ffmpeg -y -f concat -safe 0 -i input.txt -c copy '+output_video_path
		subprocess.call(concat_command.split(' '))

	if method == 'moviepy':

		raise NotImplementedError # doesn't keep audio associated, audio durations are off

		# this errors out with the warning "too many files" around 60 clips, https://github.com/Zulko/moviepy/issues/57
		mega_clip_paths = [] 
		local_clips = []
		# write out a file for every 10 clips
		for x in input_video_paths:			
			local_clips.append(VideoFileClip(x))
			if len(local_clips) == 10:
				print('Creating mega clip...')
				mega_clip = concatenate_videoclips(local_clips)
				tf = tempfile.NamedTemporaryFile().name+'.mp4'
				mega_clip.write_videofile(tf, fps=fps, audio_codec = 'pcm_s32le') 
				mega_clip_paths.append(tf)

				[x.close() for x in local_clips] 
				local_clips = []
				print('mega clips contains '+str(len(mega_clip_paths))+' paths')
		
		# get the last of the clips
		if len(local_clips) != 0:
			tf = tempfile.NamedTemporaryFile().name+'.mp4'
			mega_clip = concatenate_videoclips(local_clips)
			mega_clip.write_videofile(tf, fps=fps, audio_codec = 'pcm_s32le') 
			mega_clip_paths.append(tf)

		final = concatenate_videoclips([VideoFileClip(x) for x in mega_clip_paths])
		final.write_videofile(output_video_path, fps=fps)

		
	
	if method == 'mkv':

		raise NotImplementedError('Small timing differences')

		# concatenate in a mkv file
		mkv_path = output_video_path.replace('.mp4','.mkv')
		mkvcommand = 'mkvmerge -o '+mkv_path+' '+' + '.join(input_video_paths) 
		subprocess.call(mkvcommand.split(' '))

		# convert from mkv to mp4. To enforce a constant frame rate, need to specify a frame rate with -r
		mkv_to_mp4_command = 'ffmpeg -i '+mkv_path+' -c copy -r 30 '+output_video_path
		subprocess.call(mkv_to_mp4_command.split(' '))
	

def make_transition_clip(transition_bg_mov_path, fps, txt, duration, screensize, output_path, regenerate = False):
	
	temp_output_path = output_path.replace('.mkv', '_temp.mkv')

	if os.path.exists(temp_output_path) and regenerate == False:
		return(temp_output_path)
	else:
		transition_bg_mov = VideoFileClip(transition_bg_mov_path)
		transition_bg_mov = transition_bg_mov.set_duration(duration)

		txtClip = TextClip(txt,color='black', font="Helvetica",
	                   kerning = 5, fontsize=40)
		txtClip = txtClip.set_duration(duration)

		cvc = CompositeVideoClip( [transition_bg_mov, txtClip.set_pos('center')], size=screensize)

		cvc.write_videofile(temp_output_path.replace('.mkv','.mp4'), fps=fps, audio_fps=48000)

		# maake sure audio and video are matched in duration, and re-encode as wav
		command = 'ffmpeg -y -i '+temp_output_path.replace('.mkv','.mp4')+' -c:a pcm_s32le -c:v copy -af apad -shortest '+output_path
		print(command)
		subprocess.call(command.split(' '))
		print('Completed writing transition clip')	
		return(output_path)


def process_session(data_basepath, session, trim_videos = False, expected_number_of_trials = 45, encoding_method = 'chain'):

	FPS = 30
	REGENERATE = True

	
	for dir in ['processed', 'fps_matched', 'trimmed']:
		dir_to_create = os.path.join(data_basepath, 'lookit_data', session, dir)
		if not os.path.exists(dir_to_create):
			os.makedirs(dir_to_create)
	
	gazetracking_mp4s = [x for x in glob.glob(os.path.join(data_basepath, 'lookit_data', session, 'raw','*gazetracking*.mp4'))  if 'trimmed' not in x] 

	# match fps and re-encode the audio as wav
	[change_fps(x, FPS, regenerate = True) for x in gazetracking_mp4s]
	gazetracking_mkvs = glob.glob(os.path.join(data_basepath, 'lookit_data', session, 'fps_matched','*gazetracking*.mkv'))

	# match video and audio duration before concatenating
	if trim_videos:
		[trim_video_audio_durations(x, regenerate = True) for x in gazetracking_mkvs]
		gazetracking_mkvs = glob.glob(os.path.join(data_basepath, 'lookit_data', session, 'trimmed','*gazetracking*.mkv'))

	mkv_df = pd.DataFrame({"file" : gazetracking_mkvs})
	mkv_df['ffprobe_duration'] = [get_duration(x, 'ffprobe') for x in mkv_df.file]
	mkv_df['mediainfo_video_duration'] = [get_duration(x, 'mediainfo-video') for x in mkv_df.file]
	mkv_df['mediainfo_audio_duration'] = [get_duration(x, 'mediainfo-audio') for x in mkv_df.file]


	mkv_df['type'] = 'participant_recording'

	if mkv_df.shape[0] != expected_number_of_trials:
		warnings.warn('Trial videos are missing. Expecting '+str(expected_number_of_trials) +' videos but found '+str(mkv_df.shape[0]))
	else:
		print('Expected number of videos found ('+str(expected_number_of_trials)+')')

	
	# make the transition clips
	# get the properties of a single video
	example_video = VideoFileClip(mkv_df.file[0])

	transitions_dir = os.path.join(data_basepath, 'lookit_data', session, 'transitions')
	if not os.path.exists(transitions_dir):
		os.makedirs(transitions_dir)

	transition_clips = [] 
	for i in range(len(mkv_df.file)):
		transition_clips.append(make_transition_clip(transition_bg_mov_path= args.buffervideo, fps=FPS, txt=os.path.basename(mkv_df.file[i]).replace('_','_\n'), duration =2, screensize = example_video.size, output_path= os.path.join(transitions_dir,str(i)+'.mkv'),
			regenerate = True)) 

	transitions_df = pd.DataFrame({"file" : transition_clips})
	transitions_df['ffprobe_duration'] = [get_duration(x, 'ffprobe') for x in transitions_df.file]
	transitions_df['mediainfo_video_duration'] = [get_duration(x, 'mediainfo-video') for x in transitions_df.file]	
	transitions_df['mediainfo_audio_duration'] = [get_duration(x, 'mediainfo-audio') for x in transitions_df.file]	
	transitions_df['type'] = 'transition_video'

	#intersperse the transition clips and the real clips
	transition_records = transitions_df.to_dict('records')
	participant_recording_records = mkv_df.to_dict('records') 
	if len(participant_recording_records) != len(transition_records):
		raise ValueError('There should be an equal number of participant recordings as transition videos')
		
	combined = []
	for i in range(len(participant_recording_records)):
		combined.append(transition_records[i])
		combined.append(participant_recording_records[i])

	combined_df = pd.DataFrame(combined)
	combined_df['end_time']  =   np.cumsum(combined_df['ffprobe_duration'])
	start_times = [0] + combined_df['end_time'].tolist()
	combined_df['start_time'] = start_times[0:(len(start_times) - 1)]

	participant_videos_df = combined_df #.loc[combined_df.type == 'participant_recording']
	participant_videos_df['index'] = range(participant_videos_df.shape[0])

	# do the actual concatenation
	output_video_path = os.path.join(data_basepath, 'lookit_data', session, 'processed', session+'.mp4')	
	concat_mp4s(combined_df.file, output_video_path, "reencode", 30)
	

	# write out the metadata
	output_metadata_path = os.path.join(data_basepath, 'lookit_data', session, 'processed', session+'.csv')
	participant_videos_df.to_csv(output_metadata_path)

	# get the unique frame timestamps
	get_frame_ts_for_video(output_video_path)

	print('Time difference: '+str(round(abs(get_duration(output_video_path, 'ffprobe') - participant_videos_df.tail(1).iloc[0].end_time), 3))+' seconds')
	

def main(args):

	if args.session:
		session_dirs = [os.path.join(args.data_basepath, 'lookit_data', args.session)]
		sessions = [args.session]
	else:
		raise NotImplementedError # not tested yet; need more participants to test
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
    parser.add_argument('--buffervideo',                       
                           action='store',
                           type=str,
                           help='Path to the buffer video that will have trial labels superimposed')    
    args = parser.parse_args()
    main(args)