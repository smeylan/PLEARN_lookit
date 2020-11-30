library('ggplot2')

#https://blog.revolutionanalytics.com/2016/03/com_class_eval_metrics_r.html


get_precision_recall_f1 = function(cm, overall = F){	

	n = sum(cm) # number of instances
	nc = nrow(cm) # number of classes
	diag = diag(cm) # number of correctly classified instances per class 
	rowsums = apply(cm, 1, sum) # number of instances per class
	colsums = apply(cm, 2, sum) # number of predictions per class
	p = rowsums / n # distribution of instances over the actual classes
	q = colsums / n # distribution of instances over the predicted classes
	
	precision = diag / colsums
	recall = diag / rowsums
	f1 = 2 * precision * recall / (precision + recall) 

	if (overall){		
		accuracy = sum(diag) / n
		return(accuracy)
	} else {
		data.frame(precision, recall, f1) 
	}
}


get_confusion_matrix_for_participant = function(basedir, session_id, plot=F){
	
	human_annotations = read.csv(paste0(basedir, session_id, '/processed/', 'scm_', session_id,'.csv'), stringsAsFactors = F)

	names(human_annotations)[names(human_annotations) == 'label'] = 'human_label'

	bet_annotation_path = paste0(basedir, session_id, '/processed/', session_id, '_babyeyetracker.csv')
	header <- read.csv(bet_annotation_path, nrows = 2, header = FALSE, stringsAsFactors = FALSE)
	bet_annotations    <- read.csv(bet_annotation_path, skip = 2, header = FALSE, stringsAsFactors = F)
	colnames(bet_annotations) <- unlist(header[2,])[1:3]

	names(bet_annotations) = c('Time', 'Duration','bet_label')
	bet_annotations$Duration =  NULL

	bet_annotations$human_label = sapply(bet_annotations$Time, function(time){
		closest_index = which.min(abs(human_annotations$ms - time))	
		human_annotations[closest_index, 'human_label'][1]	
	})

	bet_annotations_filtered = subset(bet_annotations, human_label %in% c('left','right','away') & bet_label %in% c('left','right','away'))


	confusion_matrix <- as.data.frame(table(bet_annotations_filtered$human_label, 	bet_annotations_filtered$bet_label))
	
	r_confusion_matrix <- as.matrix(table(bet_annotations_filtered$human_label, 	bet_annotations_filtered$bet_label))

	session_name = strsplit(session_id,'-')[[1]][1]
	if (plot){
		p1 = ggplot(data = confusion_matrix, mapping = aes(x = Var1, y = Var2)
	) + geom_tile(aes(fill = Freq)) + geom_text(aes(label = sprintf("%1.0f", Freq)
	), vjust = 1) + scale_fill_gradient(low = "blue", high = "red"	) + xlab('Human Code') + ylab('Automated Code')  +ggtitle(paste('child:', session_name))
	
	ggsave(paste0('~/Downloads/', session_name,'_confusionMatrix.png'))
	print(p1)
		
	}
	
	rlist = list()
	rlist[['bet_annotations_filtered']] = bet_annotations_filtered
	rlist[['confusion_matrix']] = confusion_matrix
	rlist[['r_confusion_matrix']] = r_confusion_matrix	
	rlist[['plot']] = p1
	
	return(rlist)	
}


child1 = get_confusion_matrix_for_participant(basedir = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/',session_id= '9a9fe8f1-c7ba-4d57-baef-2c8fb7a79035', plot=T)
get_precision_recall_f1(child1$r_confusion_matrix)
get_precision_recall_f1(child1$r_confusion_matrix, overall=T)

child2 = get_confusion_matrix_for_participant(basedir = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/',session_id= '9cbb4790-a33d-471a-831f-20d4bad97550', plot=T)
get_precision_recall_f1(child2$r_confusion_matrix)
get_precision_recall_f1(child2$r_confusion_matrix, overall=T)

child3 = get_confusion_matrix_for_participant(basedir = '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/lookit_data/',session_id= '7dc30b41-8f08-466d-b342-7da585ba84eb', plot=T)
get_precision_recall_f1(child3$r_confusion_matrix)
get_precision_recall_f1(child3$r_confusion_matrix, overall=T)
