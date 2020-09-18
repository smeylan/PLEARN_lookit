def concat_mp4s(concatPath, glob):
		'''Concatenate a list of mp4s into a single new mp4.
		concatPath: full path to the desired new mp4 file, including
			extension vidPaths: relative paths (within paths.SESSION_DIR) to
			the videos to concatenate. Videos will be concatenated in the
			order they appear in this list.
		Return value: vidDur, the duration of the video stream of the
			concatenated mp4 in seconds. vidDur is 0 if vidPaths is empty,
			and no mp4 is created.'''

		concat = 'ffmpeg'#[paths.FFMPEG]
		inputList = ''

		# If there are no files to concat, immediately return 0.
		if not len(vidPaths):
			return 0

		# Check whether we have audio for each component file
		hasAudio = [(not videoutils.get_video_details(vid, ['audduration'], fullpath=True) == 0) for vid in vidPaths]

		# Build the concatenate command
		for (iVid, vid) in enumerate(vidPaths):
			concat = concat + ['-i', os.path.join(paths.SESSION_DIR, vid)]
			if all(hasAudio):
				inputList = inputList + '[{}:0][{}:1]'.format(iVid, iVid)
			else:
				inputList = inputList + '[{}:0]'.format(iVid)

		# Concatenate the videos
		concat = concat + ['-filter_complex', inputList + 'concat=n={}:v=1:a={}'.format(len(vidPaths), 1*(all(hasAudio))) + '[out]',
			'-map', '[out]', concatPath, '-loglevel', 'error', "-c:v", "libx264", "-preset", "slow",
			"-b:v", "1000k", "-maxrate", "1000k", "-bufsize", "2000k",
			"-c:a", "libfdk_aac", "-b:a", "128k"]

		sp.call(concat)

		# Check and return the duration of the video stream
		vidDur = videoutils.get_video_details(concatPath, 'vidduration', fullpath=True)
		return vidDur