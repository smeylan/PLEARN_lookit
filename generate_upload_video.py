from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os

def make_transition_clip(transition_bg_mov_path, txt, duration, screensize, output_path, regenerate):
	
	if os.path.exists(output_path) and regenerate == False:
		return(output_path)
	else:
		transition_bg_mov = VideoFileClip(transition_bg_mov_path)
		transition_bg_mov = transition_bg_mov.set_duration(duration)

		# txtClip = TextClip(txt,color='black', font="Helvetica",
	 #                   kerning = 1, fontsize=40)
		# txtClip = txtClip.set_duration(duration)

		# cvc = CompositeVideoClip( [transition_bg_mov, txtClip.set_pos('center')], size=screensize)

		#final_clip = concatenate_videoclips([cvc, cvc, cvc])
		final_clip = concatenate_videoclips([transition_bg_mov, transition_bg_mov, transition_bg_mov])
		final_clip.write_videofile(output_path)
		return(output_path)


transition_bg_mov_path =  '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/video_cutter/white_2s.mp4'
txt = "Your video will now upload.\nWe have a few more questions for you (the adult)\nafter it finishes uploading, but your child is done!"
screensize = (1280, 720)
output_path = '/Users/stephanmeylan/Downloads/white_6s.mp4'
regenerate = True
duration = 2
make_transition_clip(transition_bg_mov_path, txt, duration, screensize, output_path, regenerate)




transition_bg_mov_path =  '/Users/stephanmeylan/Nextcloud2/MIT/PLEARN/video_cutter/white_2s.mp4'
txt = "Your video will now upload.\nWe have a few more questions for you (the adult)\nafter it finishes uploading, but your child is done!"
screensize = (1280, 720)
output_path = '/Users/stephanmeylan/Downloads/white_6s.webm'
regenerate = True
duration = 2
make_transition_clip(transition_bg_mov_path, txt, duration, screensize, output_path, regenerate)