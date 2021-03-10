# select for double coding

# python prepare_for_doublecoding.py --session 983f28e8-40ac-4226-9968-47562ab5c8de --data_basepath /Users/stephan/dropbox/Documents/MIT/research/PLEARN

import pandas as pd
import glob
import argparse
import os

def main(args):
    
    NUM_TRIALS_TO_SAMPLE = 4

    trials_file = os.path.join(args.data_basepath, 'lookit_data', args.session, 'processed', args.session+'.csv')
    trials_df = pd.read_csv(trials_file)

    test_trials_df = trials_df.loc[trials_df.file.str.contains('test-normal')]
    selected_trials = test_trials_df.sample(NUM_TRIALS_TO_SAMPLE)

    selected_trials_file = trials_file.replace('.csv','_doublecode_list.csv')
    if not os.path.exists(selected_trials_file):
        selected_trials.to_csv(selected_trials_file, index=False)
        print('Selected '+str(NUM_TRIALS_TO_SAMPLE)+' files and output them at '+selected_trials_file)
        print('Processing complete!')
    else:
        print('Selected trials file already exists at '+selected_trials_file+'. Delete it first and run again.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Select test trials for double coding')
    parser.add_argument('--data_basepath',
                           type=str,
                           action='store',
                           help='The data root for the project (should include lookit_data as a directory, containing folders corresponding to sessions) ')
    parser.add_argument('--session',                       
                           action='store',
                           type=str,
                           help='The session identifier under lookit-data to process. If unspecified, then all sessions in `lookit_data` will be processed.')
 
    args = parser.parse_args()

    main(args)