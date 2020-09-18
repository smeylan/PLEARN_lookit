get_frame_events = function(frame_data_path, browser){
	timing_data_long = read.csv(frame_data_path, stringsAsFactors=F)
	timing_data_short = timing_data_long %>% spread(key, value, fill = NA, convert = FALSE)
names(timing_data_short)

	tds_by_event = split(timing_data_short, timing_data_short$frame_id)

	frame_events = do.call('rbind', lapply(tds_by_event, function(x){
		
		calibration_events =  subset(x, eventType == "exp-lookit-composite-video-trial:startCalibration")
		if (nrow(calibration_events) > 0){
			start_video_test_time = min(calibration_events$timestamp	)
		} else {
			start_video_test_time =  subset(x, eventType == "exp-lookit-composite-video-trial:startTestVideo")$timestamp
		}
		
		recorder_start_time = subset(x, eventType == "exp-lookit-composite-video-trial:startRecording")$timestamp
		
		
		video_stream_connection_time = subset(x, eventType == "exp-lookit-composite-video-trial:videoStreamConnection" & status == 'connected')$timestamp 
		video_stream_disconnection_time = subset(x, eventType == "exp-lookit-composite-video-trial:videoStreamConnection" & status == 'disconnected: io client disconnect')$timestamp 
		streamTime = subset(x, eventType == "exp-lookit-composite-video-trial:videoStreamConnection" & status == 'disconnected: io client disconnect')$streamTime
		recorder_end_time = subset(x, eventType == "exp-lookit-composite-video-trial:stoppingCapture")$timestamp	 
			
		return(data.frame(start_video_test_time, recorder_start_time, video_stream_connection_time, video_stream_disconnection_time,
		streamTime, recorder_end_time, stringsAsFactors=F))
	}))
	
	options(digits.secs=3)

	
	if (browser == 'chrome'){
		# recorder_start_time is the reference
		time_cols = c('start_video_test_time', 'video_stream_connection_time', 'video_stream_disconnection_time', 'recorder_end_time')
		for (colname in c(time_cols, 'recorder_start_time')){
			frame_events[[colname]] = as.POSIXlt(gsub('T',' ',frame_events[[colname]]))	
		}	
		
		for (colname in c(time_cols, 'recorder_start_time')){
			frame_events[[colname]] = 	frame_events[[colname]] - frame_events$recorder_start_time
		}
	} else if (browser == 'firefox'){
		# start_video_test_time is the reference
		time_cols = c('recorder_start_time', 'video_stream_connection_time', 'video_stream_disconnection_time', 'recorder_end_time')
		for (colname in c(time_cols, 'start_video_test_time')){
			frame_events[[colname]] = as.POSIXlt(gsub('T',' ',frame_events[[colname]]))	
		}	
		
		for (colname in c(time_cols, 'start_video_test_time')){
			frame_events[[colname]] = 	frame_events[[colname]] - frame_events$start_video_test_time
		}
	}
	
	frame_events$frame_id = sapply(strsplit(rownames(frame_events), '-'), function(x){paste(tail(x, length(x)-1), collapse='-')})
	
	frame_events$trial_index = sapply(strsplit(frame_events$frame_id,'-'), function(x){as.numeric(tail(x, 1))})
	frame_events$trial_type = 'test'
	frame_events$trial_type[grep('-p', frame_events$frame_id) ] = 'practice'
	frame_events$trial_type[(frame_events$trial_index + 3) %% 4 == 0] = 'calibration_test'	
	
	return(frame_events)	
}


get_video_durations = function(video_path, name_type='simple'){
    audio_duration_command = paste0('mediainfo --Inform="Audio;%Duration/String3%" ',
    "-of default=noprint_wrappers=1:nokey=1 ", video_path)    
    audio_duration = system(audio_duration_command, intern = T)
	audio_components = strsplit(audio_duration, ':')[[1]]
    hours = audio_components[1]
    minutes = audio_components[2]
    seconds = audio_components[3]    
	if (hours == '00'){hours = '0'} 
    if (minutes == '00'){minutes = '0'} 
    mediainfo_audio_duration = ((as.numeric(hours) * 60 * 60) + (as.numeric(minutes) * 60) + as.numeric(seconds))
    
    video_duration_command = paste0('mediainfo --Inform="Video;%Duration/String3%" ',
    "-of default=noprint_wrappers=1:nokey=1 ", video_path)    
    video_duration = system(video_duration_command, intern = T)
	video_components = strsplit(video_duration, ':')[[1]]
    hours = video_components[1]
    minutes = video_components[2]
    seconds = video_components[3]    
	if (hours == '00'){hours = '0'} 
    if (minutes == '00'){minutes = '0'} 
    mediainfo_video_duration = ((as.numeric(hours) * 60 * 60) + (as.numeric(minutes) * 60) + as.numeric(seconds))
    rdf = data.frame(video_path, mediainfo_audio_duration , mediainfo_video_duration)
    
    if (name_type == 'simple'){
    		rdf$frame_id = gsub('.mp4', '', tail(strsplit(video_path, '_')[[1]], 1))
    } else if (name_type == 'lookit'){
		rdf$frame_id = get_frame_id_from_path(video_path)
	}    
    return(rdf)
}

get_gaze_code_timings = function(gaze_code_path){
	gaze_codes = read.csv(gaze_code_path, stringsAsFactors=F)
	gaze_codes$frame_id = sapply(gaze_codes$filename, get_frame_id_from_path)
	by_frame = split(gaze_codes, gaze_codes$frame_id)
	earliest_latest = do.call('rbind', lapply(by_frame, get_nonfrozen))	
	for (col in  c('earliest_gaze', 'latest_gaze', 'earliest_nonfrozen_gaze', 'latest_nonfrozen_gaze')){
		earliest_latest[[col]] = (earliest_latest[[col]] / 1000	)
	}
	return(earliest_latest)	
}


get_timecourse_info_for_videos = function(base_video_path, frame_data_path, name_type, browser, gaze_code_path=NULL){
	
	video_paths = Sys.glob(paste(base_video_path,'/*.mp4', sep=''))	
	video_durations = do.call('rbind', lapply(video_paths, function(path){
		get_video_durations(path, name_type)}))	
	frame_events = get_frame_events(frame_data_path, browser)
	#frame_events$approx_disambig_time = 5.1 #2s white, 2s with stims onscreen, 1.1 to disambig
	
	merged_data = merge(video_durations, frame_events, by='frame_id')
	
	if (!is.null(gaze_code_path)){		
		earliest_latest = get_gaze_code_timings(gaze_code_path)
		
		merged_data = merge(merged_data, earliest_latest, by='frame_id')
		#merged_data$delay_and_nonfrozen = merged_data$nonfrozen_duration + merged_data$delay_recording_after_stim		
		
		target_cols = c('frame_id','recorder_start_time', 'recorder_end_time', 'mediainfo_video_duration', 'mediainfo_audio_duration', 'trial_type', 'trial_index','earliest_nonfrozen_gaze', 'latest_nonfrozen_gaze', 'earliest_gaze', 'latest_gaze', 'start_video_test_time')
		# 'stream_start_to_end' is much higher -- transmission time / websocket open?
		# StreamTime is very, very close torecord_start_to_end
		durations = merged_data[,target_cols]	
	} else {
		durations = merged_data[,target_cols]	
	}	

	return(durations)	
}

plot_timecourse_data = function(durations){
	melted_durations = melt(durations, id.vars=c("frame_id", "trial_type", "trial_index"))

	melted_durations$variable = factor(melted_durations$variable)
	melted_durations$value = as.numeric(melted_durations$value)
	
	melted_durations$frame_id = factor(melted_durations$frame_id)
	
	ggplot(melted_durations) + geom_point(aes(x=frame_id, y=value, color=variable, shape=variable)) + theme_classic(
	) + geom_line(aes(x=frame_id, y=value, color=variable, group=variable), alpha=.25) + ylab('Duration in Seconds'
	) + theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) + facet_wrap(~ trial_type, scales='free') 
}

get_nonfrozen = function(frame){
	non_frozen = subset(frame, !(label %in% c('frozen', '')))
 	non_frozen  = non_frozen[order(non_frozen$ms),]
	
	earliest_nonfrozen_gaze = head(non_frozen, n=1)$ms
 	latest_nonfrozen_gaze = tail(non_frozen, n = 1)$ms
 	frame_id = unique(non_frozen$frame_id) 	

	earliest_gaze = head(frame, n = 1)$ms
	latest_gaze = tail(frame, n = 1)$ms 
 	 	
 	return(data.frame(earliest_gaze, latest_gaze, earliest_nonfrozen_gaze, latest_nonfrozen_gaze, frame_id))
}

get_frame_id_from_path = function(video_path){
	frame_id = strsplit(tail(strsplit(video_path,'/')[[1]], 1), '_')[[1]][3]
	elements = strsplit(frame_id, '-')[[1]]
	return(paste(tail(elements, length(elements)-1), collapse='-'))	
}

plot_normalized_frame_events = function(normalized_frame_events, browser){ 
	normalized_frame_events$trial_index = NULL
	melted_timeline = melt(normalized_frame_events, id.vars=c("frame_id", "trial_type"))
	melted_timeline $variable = factor(melted_timeline $variable)
	melted_timeline $value = as.numeric(melted_timeline $value)
	melted_timeline $frame_id = factor(melted_timeline $frame_id)
	
	p1 = ggplot(subset(melted_timeline, trial_type == 'test'  )) + geom_point(aes(y=frame_id, x=value, color=variable, shape=variable)
	) + scale_shape_manual(values=seq(0,15)) + theme_classic(
	) + ylab('Trial'
	)  + theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) + geom_vline(xintercept = 12, linetype='dashed', color='gray')
	
	if (browser == 'firefox'){
		p1 = p1 + xlab('Seconds (Firefox: 0 = startTestVideo = earliest_gaze (frozen))')	
	} else if (browser == 'chrome'){
		p1 = p1 + xlab('Seconds (Chrome: 0 = startRecording = earliest_gaze = earliest_nonfrozen_gaze)')	
	}
	return(p1)
 }
 
 plot_gaze_codes = function(gaze_code_path){
	gaze_codes = read.csv(gaze_code_path, stringsAsFactors = F)
	gaze_codes$X = NULL
	gaze_codes$frame_id = sapply(gaze_codes$filename, get_frame_id_from_path)
	gaze_codes$trial_index = sapply(strsplit(gaze_codes$frame_id,'-'), function(x){as.numeric(tail(x, 1))})
	gaze_codes$trial_type = 'test'
	gaze_codes$trial_type[grep('-p', gaze_codes$frame_id) ] = 'practice'
	gaze_codes$calibration = 'normal'
	gaze_codes$calibration[grep('calibration', gaze_codes$frame_id) ] = 'calibration'	
	
	ggplot(subset(gaze_codes, label != '')) + geom_point(aes(x=ms, y=frame_id, color=label)) + theme_bw() + geom_vline(xintercept=5100) + facet_grid(calibration~trial_type)
	#ggsave('~/Downloads/gaze_codes.pdf', width=10, height =4)	
}