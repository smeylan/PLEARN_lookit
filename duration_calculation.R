library('tidyr')
library('ggplot2')
library('reshape2')
setwd('~/Nextcloud2/MIT/PLEARN/lookit/')
source('duration_calculation_helper.R')

# Run 9 -- deprecated
# frame_data_path = '~/Downloads/Can-you-find-the--nops---Watch-videos-and-read-a-storybook-about-new-and-familiar-words_framedata_per_session(1)/Can-you-find-the--nops---Watch-videos-and-read-a-storybook-about-new-and-familiar-words_a2ac0adc-64db-4576-8543-2425f1b6d468_frames.csv'
# base_video_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/run9'
# durations = get_timecourse_info_for_videos(base_video_path, frame_data_path, name_type = 'lookit')	
# plot_timecourse_data(durations)
	
# Lindsay Pilot	
frame_data_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/lindsay_pilot/Can-you-find-the--wugs---Watch-videos-and-read-a-storybook_d726312d-be7e-4839-b955-7a2c2bbf6ecf_frames.csv'
base_video_path = "/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/lindsay_pilot"
gaze_code_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/lindsay_pilot/gaze_codes.csv'

source('duration_calculation_helper.R')
durations = get_timecourse_info_for_videos(base_video_path, frame_data_path, browser='firefox', name_type = 'lookit', gaze_code_path)	
plot_normalized_frame_events(durations, browser='firefox')
ggsave('~/Downloads/normalized_frame_events_participant1_firexfox.png', width=8, height =6)
#plot_gaze_codes(gaze_code_path)


# Jonah Pilot
frame_data_path = '/Users/stephanmeylan/Downloads/Can-you-find-the--wugs---Watch-videos-and-read-a-storybook_framedata_per_session(1)/Can-you-find-the--wugs---Watch-videos-and-read-a-storybook_7bb78a64-4ded-4c46-bf6c-6d40d2566420_frames.csv'
base_video_path = "/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/jonah_pilot"
gaze_code_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/jonah_pilot/gaze_codes.csv'

source('duration_calculation_helper.R')
durations = get_timecourse_info_for_videos(base_video_path, frame_data_path, browser='chrome', name_type = 'lookit', gaze_code_path)	
plot_normalized_frame_events(durations, browser='chrome')
ggsave('~/Downloads/normalized_frame_events_participant2_chrome.png', width=8, height =6)
plot_gaze_codes(gaze_code_path)

durations = get_timecourse_info_for_videos(base_video_path, frame_data_path, name_type = 'lookit', gaze_code_path)	
plot_normalized_frame_events(durations)
ggsave('~/Downloads/normalized_frame_events_jonah.png', width=8, height =5)
plot_gaze_codes(gaze_code_path)


# assuming that there is a correspondence between the begining of the participant video and the the begining of the stimulus video


durations[,c('frame_id','mediainfo_audio_duration', 'mediainfo_video_duration')]
sum(durations$mediainfo_audio_duration)
sum(durations$mediainfo_video_duration) 

durations$longest_duration = mapply(max, durations$mediainfo_audio_duration, durations$mediainfo_video_duration)
durations$shortest_duration = mapply(min, durations$mediainfo_audio_duration, durations$mediainfo_video_duration)
((sum(durations$longest_duration) / 60) -9) * 60 #over  by 1.45s
((sum(durations$shortest_duration) / 60) -9) * 60 #under  by 13.8s

# pairwise max of these mapp
# video duration unless it is shorter than the audio duration, in which case audio duration

sum(durations$mediainfo_video_duration[which(durations$mediainfo_video_duration > durations$mediainfo_audio_duration)],
durations$mediainfo_audio_duration[which(durations$mediainfo_video_duration < durations$mediainfo_audio_duration)])
sum(durations$mediainfo_audio_duration) # audio duration is much shorter

