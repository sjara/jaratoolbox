"""
Classes for storing video metadata.
"""

cameraParams = {}

cameraParams['IR_webcam_640x480_30fps_VP9'] = {
    'camera':'USB webcam with 10 IR LED',
    'camera_URL':'https://www.amazon.com/dp/B07PPN7TXQ',
    'framerate':30,
    'resolution':[640,480],
    'pixel_format':'YV12',
    'codec':'VP9',
    'approx_file_size':'2.4 MB/min'
}


class VideoParameters:
    """
    Class for storing metadata associated with a video.
    """
    def __init__(self, subject, date, sessionType, videoFile, behavFile, cameraParams):
        self.subject = subject
        self.date = date
        self.sessionType = sessionType
        self.videoFile = videoFile
        self.behavFile = behavFile
        self.cameraParams = cameraParams
    def __str__(self):
        return f'{self.subject} [{self.date}] {self.sessionType}  {self.videoFile}'


class Videos:
    """
    Class for storing a collection of video metadata associated with a subject.
    """
    def __init__(self, subject):
        self.subject = subject
        self.sessions = []
    def add_session(self, date, sessionType, videoFile, behavFile, cameraParams):
        oneSession = VideoParameters(self.subject, date, sessionType, videoFile,
                                     behavFile, cameraParams)
        self.sessions.append(oneSession)
    def __str__(self):
        fullStr = ''
        for session in self.sessions:
            fullStr += str(session)
            fullStr += '\n'
        return fullStr
   
      
