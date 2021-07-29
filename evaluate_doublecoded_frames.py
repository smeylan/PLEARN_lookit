import pandas as pd
import numpy as np
import argparse
import glob
import os
from sklearn.metrics import cohen_kappa_score

def main(args):
	participants_df = pd.read_csv(args.participants_file)
	participants_df = participants_df.fillna('')
	doublecoded_frames = list()

	for participant in participants_df.to_dict('records'):

		# read in the main transcription file (csv)		
		first_coder = participant['main_coder'].split(', ')[0]	
		if first_coder == '':
			print('First coder is undefined for '+participant['id'])	
			continue
		second_coder = participant['double_coder'].split(', ')[0]
		if second_coder == '':
			print('Second coder is undefined for '+participant['id'])	
			continue

		print('Coders are defined for '+participant['id']+'!')


		participant_annotation_path = os.path.join(args.data_basepath,'lookit_data/'+participant['id']+'/processed', first_coder+'_'+participant['id']+'.csv')

		participant_annotation_df = pd.read_csv(participant_annotation_path)
		participant_annotation_df['id'] = participant['id']

		# read in the doublecode transcription file (csv)
		doublecode_annotation_path = os.path.join(args.data_basepath,'lookit_data/'+participant['id']+'/processed', second_coder +'_'+participant['id']+'_doublecode.csv')

		doublecode_annotation_df = pd.read_csv(doublecode_annotation_path)[['ms','frame_id','label']]
		doublecode_annotation_df.columns = ['ms','frame_id','doublecode_label']

		# relabel the columns of doublecoode to allow for merging
		
		# merge based on trial id and time
		participant_merged = doublecode_annotation_df.merge(participant_annotation_df, on = ['ms', 'frame_id'])
		
		# add to the collection of double-coded trials
		doublecoded_frames.append(participant_merged)
	

	doublecoded_frames_df = pd.concat(doublecoded_frames)
	# evaluate ck on the whole collection

	number_of_participants = len(np.unique(doublecoded_frames_df['id']))
	print("Number of participants in double-coded set:")
	print(number_of_participants)

	ck = cohen_kappa_score(doublecoded_frames_df['label'], doublecoded_frames_df['doublecode_label'])
	print("Cohen's Kappa:")
	print(ck)

	# save a csv with the resulting data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Computes Cohen's Kappa using doublecoded files")
    parser.add_argument('--data_basepath',
                           type=str,
                           action='store',
                           help='The data root for the project (should include lookit_data as a directory, containing folders corresponding to sessions) ')
    parser.add_argument('--participants_file',                       
                           action='store',
                           type=str,
                           help='Path to the participants file which specifies which main and double-coded file should be evaluated for each participant')
   
    
    args = parser.parse_args()
    
    main(args)