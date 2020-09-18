ffmpeg -y -i end-video.mp4  -ss 0 -c:v libvpx -b:v 4000k -maxrate 4000k -bufsize 2000k -speed 2 end-video.webm
ffmpeg -y -i end-practice-begin-test-video.mp4  -ss 0 -c:v libvpx -b:v 4000k -maxrate 4000k -bufsize 2000k -speed 2  end-practice-begin-test-video.webm
ffmpeg -y -i gazetracking-position-check-video.mp4  -ss 0 -c:v libvpx -b:v 4000k -maxrate 4000k -bufsize 2000k -speed 2 gazetracking-position-check-video.webm
ffmpeg -y -i end-gazetracking-begin-storybook-video.mp4  -ss 0 -c:v libvpx -b:v 4000k -maxrate 4000k -bufsize 2000k -speed 2 end-gazetracking-begin-storybook-video.webm
ffmpeg -y -i start-video.mp4  -ss 0 -c:v libvpx -b:v 4000k -maxrate 4000k -bufsize 2000k -speed 2 start-video.webm
