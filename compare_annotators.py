# python compare_annotators.py --data_basepath ../ --session 9cbb4790-a33d-471a-831f-20d4bad97550 --gold_tagger scm
import pandas as pd
import numpy as np
import argparse
import glob
import os
import itertools
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics import f1_score
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt

def plot_confusion_matrix(y_true, 
                        y_pred,
                          target_names,                          
                          annotator_name,
                          gold_tagger,                         
                          plot_filename,  
                          title='Confusion matrix (rows sum to 1)',
                          cmap=None,
                          normalize=True):
    """
    given a sklearn confusion matrix (cm), make a nice plot

    Arguments
    ---------
    cm:           confusion matrix from sklearn.metrics.confusion_matrix

    target_names: given classification classes such as [0, 1, 2]
                  the class names, for example: ['high', 'medium', 'low']

    title:        the text to display at the top of the matrix

    cmap:         the gradient of the values displayed from matplotlib.pyplot.cm
                  see http://matplotlib.org/examples/color/colormaps_reference.html
                  plt.get_cmap('jet') or plt.cm.Blues

    normalize:    If False, plot the raw numbers
                  If True, plot the proportions

    Usage
    -----
    plot_confusion_matrix(cm           = cm,                  # confusion matrix created by
                                                              # sklearn.metrics.confusion_matrix
                          normalize    = True,                # show proportions
                          target_names = y_labels_vals,       # list of names of the classes
                          title        = best_estimator_name) # title of graph

    Citiation
    ---------
    http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html

    """
    cm = confusion_matrix(y_true, y_pred, labels = target_names)

    accuracy = np.trace(cm) / np.sum(cm).astype('float')
    misclass = 1 - accuracy

    if cmap is None:
        cmap = plt.get_cmap('Blues')

    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()

    if target_names is not None:
        tick_marks = np.arange(len(target_names))
        plt.xticks(tick_marks, target_names, rotation=45)
        plt.yticks(tick_marks, target_names)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]


    thresh = cm.max() / 1.5 if normalize else cm.max() / 2
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        if normalize:
            plt.text(j, i, "{:0.4f}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
        else:
            plt.text(j, i, "{:,}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")


    plt.tight_layout()
    plt.ylabel('Gold standard label ('+gold_tagger+')')
    plt.xlabel('Annotator label ('+annotator_name+')\naccuracy={:0.4f}; misclass={:0.4f}'.format(accuracy, misclass))
    plt.savefig(plot_filename)

def main(args):   

    if args.session is None:
        raise NotImplementedError # need to think through how to iterate over sessions
    else:
        filenames = glob.glob(os.path.join(args.data_basepath,'lookit_data', args.session ,'processed', '*_'+args.session+'.csv'))
    print(filenames)

    annotations = {}
    for filename in filenames:
        # get the initial from the 
        annotator_initial = os.path.basename(filename).split('_')[0]
        annotations[annotator_initial] = pd.read_csv(filename)

    # choose the gold standard annotation
    gold_annotation_data = annotations[args.gold_tagger][['ms','label']]
    # rename the columns for the gold data
    gold_annotation_data.columns = ['ms','gold_label'] 

    # iterate over the targets, comparing the target to the gold annotation 
    score_store = []
    for annotator_name, annotator_data in annotations.items():
        if annotator_name == args.gold_tagger:
            pass
        else:
            # merge the two by taking the intersection of labeled frames                        
            merged = gold_annotation_data.merge(annotator_data)
            f1 = f1_score(merged.label, merged.gold_label, average='weighted')
            ck = cohen_kappa_score(merged.label, merged.gold_label)
            score_store.append({'f1': f1, 'ck': ck, 'annotator': annotator_name, 'gold':args.gold_tagger})                        
            plot_confusion_matrix(merged.gold_label, merged.label, np.unique(merged.gold_label), annotator_initial, args.gold_tagger, plot_filename = annotator_name+'_confusion_matrix.png')

    score_df = pd.DataFrame(score_store)
    print('Scores: ')
    print(score_df)
    print('Complete!')    

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
    parser.add_argument('--gold_tagger',                       
                           type=str,
                           action='store',                           
                           help='initials of the annotator to use as the gold standard')
    
    args = parser.parse_args()
    
    main(args)