library('tidyr')
library('ggplot2')
library('reshape2')
setwd('~/Nextcloud2/MIT/PLEARN/lookit/')
source('duration_calculation_helper_v2.R')

# timed pilot
frame_data_path = '/Users/stephanmeylan/Downloads/Can-you-find-the--wugs---Watch-videos-and-read-a-storybook_framedata_per_session(2)/Can-you-find-the--wugs---Watch-videos-and-read-a-storybook_0dca467b-9332-40f2-9b69-cb0caa557317_frames.csv'
base_video_path = "/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/timed_pilot"
browser = 'firefox'

source('duration_calculation_helper.R')
durations = get_timecourse_info_for_videos(base_video_path, frame_data_path, browser, name_type = 'lookit')	
plot_normalized_frame_events(durations,'firefox_nogaze')
ggsave('~/Downloads/normalized_frame_events_participant3_firefox.png', width=8, height =6)
plot_gaze_codes(gaze_code_path)
name_type = 'lookit'




frame_data_path = '/Users/stephanmeylan/Downloads/Can-you-find-the--wugs---Watch-videos-and-read-a-storybook_framedata_per_session(3)/Can-you-find-the--wugs---Watch-videos-and-read-a-storybook_3ccbff98-1a8d-4aa1-859f-f8adfcd5d00f_frames.csv'
base_video_path = "/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/version1/timed_pilot_chrome"
browser = 'chrome'

durations = get_timecourse_info_for_videos(base_video_path, frame_data_path, browser, name_type = 'lookit')	
plot_normalized_frame_events(durations,'chrome_nogaze')
ggsave('~/Downloads/normalized_frame_events_participant4_firefox.png', width=8, height =6)
