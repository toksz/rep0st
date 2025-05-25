from absl import flags

FLAGS = flags.FLAGS

# Video Processing
flags.DEFINE_integer('rep0st_video_keyframe_interval', 1,
                    'Extract keyframe every N seconds')
flags.DEFINE_integer('rep0st_video_max_keyframes', 100,
                    'Maximum number of keyframes to extract per video')
flags.DEFINE_integer('rep0st_video_max_duration', 300,
                    'Maximum video duration in seconds to process')
flags.DEFINE_integer('rep0st_video_frame_batch_size', 10,
                    'Number of frames to process in parallel')
flags.DEFINE_integer('rep0st_video_max_upload_size_mb', 200,
                    'Maximum video upload size in MB')

# Search Settings
flags.DEFINE_integer('rep0st_video_min_matches', 3,
                    'Minimum number of matching frames to consider videos similar')
flags.DEFINE_float('rep0st_video_similarity_threshold', 0.8,
                    'Minimum similarity score (0-1) for frame matches')