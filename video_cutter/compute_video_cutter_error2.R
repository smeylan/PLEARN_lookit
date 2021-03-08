# trying to find the best inter-stimulus interval and trial duration for cutting the OBS recording

library('ggplot2')
timepoints = rbind(
data.frame(
event = 'start',
trial = 22,
time = 297.192),
data.frame(
event = 'end',
trial = 22,
time = 307.172),
data.frame(
event = 'start',
trial = 32,
time = 409.43),
data.frame(
event = 'end',
trial = 32,
time = 419.40))


library("rjson")
cut <- fromJSON(file = "/Users/stephan/Dropbox (MIT)/Documents/MIT/research/PLEARN/video_cutter/order2_cut.json")

time_error = function(cut, time_row){
	if (time_row$event == 'start'){
		time = cut[[5]]$start_time + (time_row$trial - 1)*(cut[[5]]$trial_duration + 
	cut[[5]]$pretrial_duration)	
	} else if (time_row $event == 'end'){
		time = cut[[5]]$start_time + (time_row$trial)*(cut[[5]]$trial_duration) + 
	(time_row$trial - 1)*(cut[[5]]$pretrial_duration)	
	}
	error = time - time_row$time
	return(error)
}


sapply(1:4, function(x){time_error(cut, timepoints[x,])})

pretrial_durations = seq(from=1.25, to=1.3, by=.001)
trial_durations = seq(from=9.93, to=9.96, by=.005)
length(pretrial_durations) * length(trial_durations)

scores = do.call('rbind', lapply(trial_durations, function(trial_duration){
	do.call('rbind', lapply(pretrial_durations, function(pretrial_duration){	

		cut[[5]]$pretrial_duration = pretrial_duration
		cut[[5]]$trial_duration = trial_duration		
		abs_mean_error = mean(abs(sapply(1:4, function(x){time_error(cut, timepoints[x,])})))
		return(data.frame(pretrial_duration, trial_duration, abs_mean_error))
	
}))}))

ggplot(data = scores, aes(x=trial_duration, y=pretrial_duration, fill=abs_mean_error)) + geom_tile() +
 scale_fill_gradient2(low = "blue", high = "red", mid = "white",midpoint = 0, limit = c(-1,1), space = "Lab")



head(scores[order(scores$abs_mean_error),], n=20)