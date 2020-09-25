import json
import pandas as pd
import numpy as np
import copy

input_lookit_json_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit/lookit_videotrials.json'
output_lookit_json_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit/lookit_generated_videotrials.json'
practice_trials_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit/practice_items.csv'
test_trials_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit/group1_book_test_ordered.csv'
# receptive_trials_path = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit/plearn_receptiveTask_datasource.csv'
order = "1"


with open(input_lookit_json_path) as f:
  data = json.load(f)

example_receptive_trial = data['frames']['sample-intermodal-trial-2']
example_calibration_trial = data['frames']['sample-calibration-trial']
# receptive_trials = pd.read_csv(receptive_trials_path)
# receptive_trials = receptive_trials.loc[receptive_trials.order == int(order)]

# Gaze-Tracking / Receptive task
gazetracking_practice_frames = []
gazetracking_test_frames = []

calibration_trial = copy.deepcopy(example_calibration_trial)
[calibration_trial.pop(x, None) for x in ['sources', 'altSources','musicSources']]
calibration_trial['calibrationLength'] = 3000

j=0
for i in ['p1','p2','p3','p4'] + list(range(1,33)):
	#for i in ['p1','p2'] + list(range(1,3)):
	j +=1
	receptive_trial = copy.deepcopy(example_receptive_trial)
	receptive_trial['video']['source'] = str(i)
	isPractice = 'p' in str(i) #practice vs. test
	hasCalibration = ((j+ 3) % 4) == 0 # calibration vs. normal
	
	if isPractice:
		
		if hasCalibration:
			calibration_frame_name = 'gazetracking-practice-calibration-'+str(i)
			gazetracking_practice_frames.append(calibration_frame_name)
			data['frames'][calibration_frame_name] = calibration_trial
		
		frame_name = 'gazetracking-practice-normal-'+str(i)
		gazetracking_practice_frames.append(frame_name)
		data['frames'][frame_name] = receptive_trial

	else: 
		if hasCalibration:
			calibration_frame_name = 'gazetracking-test-calibration-'+str(i)
			gazetracking_test_frames.append(calibration_frame_name)
			data['frames'][calibration_frame_name] = calibration_trial		
		
		frame_name = 'gazetracking-test-normal-'+str(i)
		gazetracking_test_frames.append(frame_name)
		data['frames'][frame_name] = receptive_trial

	if (j - 4) == 8:
		gazetracking_test_frames.append('gazetracking-quarter-finished')

	if (j - 4) == 16: 
		# add 2 frames for a position check at the end of the 16th test trial
		gazetracking_test_frames.append('gazetracking-half-finished')

	if (j - 4) == 17: 	
		gazetracking_test_frames.append('gazetracking-position-check-video')
		gazetracking_test_frames.append('gazetracking-position-check')

	if (j - 4) == 24:
		gazetracking_test_frames.append('gazetracking-threequarters-finished')



data['sequence'] = [
		"signpost",
        "video-config",
        "video-consent",
        "instructions-gazetracking",        
        "audio-test-at-start",
        "positioning-instructions",                
        "start-video"] + gazetracking_practice_frames + \
        ["end-practice-begin-test-video"] + \
        gazetracking_test_frames + \
        ["end-gazetracking-begin-storybook-video", 
        "instructions-storybook",        
        "instructions-storybook-addition",        
        "storybook-positioning-test",        
        'start-video-recording',
        "storybook-plearn",
        "end-video",
        "stop-video-capture",        
        "exit-survey"]

# Storybook / Expressive task

example_storybook_trial = data['frames']['storybook-plearn']['frameList'][0]
print(example_storybook_trial)


practice_trial_records = pd.read_csv(practice_trials_path)
print(practice_trial_records.iloc[0])
test_trial_records = pd.read_csv(test_trials_path)
print('test trial recordings')
print(test_trial_records.iloc[0])
trial_records = pd.concat([practice_trial_records, test_trial_records])

i = 0 
generated_trials = []

# title card
storybook_trial = example_storybook_trial.copy()
storybook_trial['images'][0]['id'] = 'storybook_title'
storybook_trial['images'][0]['src'] = 'https://umzy19bu4.ddns.net/plearn/order'+order+'/img/0_title.png'
storybook_trial['parentTextBlock']['text'] = "Let's read this book! It's called \"What's Here? A book about different things in different places\""
#storybook_trial['startSessionRecording'] = True
generated_trials.append(copy.deepcopy(storybook_trial))


for trial_record in trial_records.to_dict('records'):

	i+=1
	print(str(i)+': '+trial_record['s_form'])

	if (np.isnan(trial_record['Trial'])):
		trial_record['Trial'] = i+1 # hack for the practice items -- set equal to i + 1 (book is 1)
		isPractice = True
	else:
		isPractice = False

	# page 1	
	storybook_trial = example_storybook_trial.copy()
	storybook_trial['images'][0]['src'] = 'https://umzy19bu4.ddns.net/plearn/order'+order+'/img/'+str(i)+'_'+trial_record['s_form']+'_0.png'	
	
	storybook_trial['parentTextBlock']['text'] = "Look! There's one "+ trial_record['s_form']+'! Can you say "'+trial_record['s_form']+'"?'
	storybook_trial['images'][0]['id'] = 'storybook_'+str(i)+'_1'

	if i == 1:
		storybook_trial['parentTextBlock']['title'] = "For parent/caregiver:"
	else:
		if isPractice:
			storybook_trial['parentTextBlock']['title'] = str(i)+' of 20' 
		else: 
			storybook_trial['parentTextBlock']['title'] = str(i)+'A of 20' 
	
	#if i in range(1,3) or i in range(5,7) :
	generated_trials.append(copy.deepcopy(storybook_trial))
	
	if not isPractice:
		# generate page 2		
		storybook_trial = example_storybook_trial.copy()
		storybook_trial['images'][0]['src'] = 'https://umzy19bu4.ddns.net/plearn/order'+order+'/img/'+str(i)+'_'+trial_record['s_form']+'_1.png'		
		storybook_trial['parentTextBlock']['title'] = str(i)+'B of 20' 
		storybook_trial['parentTextBlock']['text'] = "What's here?"
		storybook_trial['images'][0]['id'] = 'storybook_'+str(i)+'_2'
		#if i in range(5,7):				
		generated_trials.append(copy.deepcopy(storybook_trial))			


# end card
storybook_trial = example_storybook_trial.copy()
storybook_trial['images'][0]['id'] = 'storybook_end'
storybook_trial['images'][0]['src'] = 'https://umzy19bu4.ddns.net/plearn/order'+order+'/img/20_the_end.png'
#storybook_trial['endSessionRecording'] = True # end of recordings will now be in a separate frame of type stop-recording-with-video
storybook_trial['parentTextBlock']['title'] = ''
storybook_trial['parentTextBlock']['text'] = "The end! Great job!"
generated_trials.append(copy.deepcopy(storybook_trial))
data['frames']['storybook-plearn']['frameList'] = generated_trials


with open(output_lookit_json_path, 'w') as f:
	json.dump(data, f)


# [x] get the title frame in
# [x] get the end frame in
# [X] need to add the frames to the frame order (for intermodal)
# [X] make sure that there are calibration items in the intermodals
# [X] make sure everything has an id 
