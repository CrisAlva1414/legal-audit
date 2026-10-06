class Video:
    title: str
    duration: int


def duration_in_minutes(video: Video):
    return video.duration // 60