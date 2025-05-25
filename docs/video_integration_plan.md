# Video Integration Plan for rep0st

## Overview
This document outlines the comprehensive plan to add video support to rep0st's reverse search functionality. The goal is to allow users to search for similar videos and check if a video has been previously posted on pr0gramm.com.

## 1. Core System Updates

### 1.1 Database Changes

```sql
-- New frame_info table to store video frame metadata
CREATE TABLE frame_info (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    frame_number INTEGER NOT NULL,
    timestamp FLOAT NOT NULL,
    is_keyframe BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add frame_number and frame_info_id to feature_vector
ALTER TABLE feature_vector 
    ADD COLUMN frame_number INTEGER,
    ADD COLUMN frame_info_id INTEGER REFERENCES frame_info(id);

-- Create indices
CREATE INDEX idx_frame_info_post_id ON frame_info(post_id);
CREATE INDEX idx_frame_info_post_id_frame_number ON frame_info(post_id, frame_number);
CREATE INDEX idx_frame_info_post_id_timestamp ON frame_info(post_id, timestamp);
CREATE INDEX idx_feature_vector_frame_info ON feature_vector(frame_info_id);

-- Create video-specific vector index
CREATE INDEX feature_vector_post_type_video_vec_approx 
    ON feature_vector USING hnsw (vec vector_l2_ops) 
    WITH (m = 16, ef_construction = 64)
    WHERE post_type = 'VIDEO';
```

### 1.2 Configuration Updates

Add new configuration flags in respective modules:

```python
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
```

## 2. Component Updates

### 2.1 Media Service Enhancements

Key changes to `media_service.py`:
- Add video frame extraction with metadata (frame number, timestamp, keyframe flag)
- Implement frame sampling and keyframe detection (using ffmpeg, OpenCV)
- Add video format validation and upload size/duration checks
- Implement frame batching for better performance
- Add robust error handling for video decoding
- Security: validate file types, scan for malware, limit upload size
- Add fallback mechanisms for unsupported codecs or corrupt files

### 2.2 Feature Service Updates

Changes to `feature_service.py`:
- Add video-specific feature extraction (reuse image pipeline for frames)
- Implement parallel frame processing and batching
- Store frame metadata in `frame_info` and link to `feature_vector`
- Add progress tracking for video processing
- Enforce limits on number of frames/features per video
- Stop processing once limits are reached and log warnings

### 2.3 Search Service Modifications

Updates to `post_search_service.py`:
- Implement video similarity search: query all frames, aggregate matches by video
- Add frame matching logic and temporal alignment (group nearby matches)
- Implement result aggregation and match confidence scoring
- Limit number of candidate matches for performance
- Backward compatibility: ensure image search is unaffected
- Rank videos based on the number of matching frames and their temporal alignment

### 2.4 API and Frontend Updates

Changes required for web interface:
- Add video upload support (with file type, size, and duration validation)
- Add video preview capability and progress indicators
- Show frame-level matches in results, with timestamp markers
- Add clear error messages for upload/processing failures
- Security: sanitize uploads, limit concurrent processing
- Implement chunked and resumable uploads for large files

## 3. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)

1. Database Schema Updates
   - Create new tables and indices
   - Add migration scripts
   - Update ORM models

2. Video Processing Core
   - Implement enhanced video frame extraction
   - Add video metadata handling
   - Set up parallel processing infrastructure
   - Add error handling and validation

### Phase 2: Feature Extraction (Week 2-3)

1. Video Feature Processing
   - Implement keyframe detection and frame sampling
   - Add frame metadata extraction
   - Set up batch processing pipeline
   - Enforce frame/feature limits

2. Storage and Indexing
   - Implement frame data storage
   - Set up feature vector indexing for videos
   - Add data validation and error handling

### Phase 3: Search Implementation (Week 3-4)

1. Search Algorithm
   - Implement frame matching logic
   - Add temporal alignment and similarity scoring
   - Implement result aggregation
   - Limit candidate matches for performance

2. Performance Optimization
   - Add caching layer
   - Implement batch processing
   - Optimize database queries and indices
   - Add index optimizations

### Phase 4: Frontend Integration (Week 4-5)

1. UI Updates
   - Add video upload support and validation
   - Implement progress tracking and error messages
   - Add video preview functionality
   - Create results visualization with frame/timestamp markers

2. API Enhancement
   - Add video-specific endpoints
   - Implement progress reporting
   - Add error handling and documentation

## 4. Testing Strategy

### 4.1 Unit Tests
- Video frame extraction and validation
- Feature vector generation for frames
- Frame matching and aggregation
- Temporal alignment
- Result aggregation and scoring

### 4.2 Integration Tests
- End-to-end video processing
- Search functionality (video and image)
- Database operations and migrations
- API endpoints and error handling

### 4.3 Performance Tests
- Large video processing
- Concurrent video uploads
- Search performance
- Database query optimization
- Define specific metrics for performance tests:
  - Processing time per frame
  - Search response time
  - Memory usage during batch processing
- Add test cases for edge scenarios, such as very short or very long videos

## 5. Monitoring and Maintenance

### 5.1 New Metrics to Track
- Video upload success rate
- Video processing time per frame
- Frame extraction performance
- Feature generation speed
- Search response times
- Storage usage
- Error rates
- Cache hit rates

### 5.2 Alerts
- Video processing failures
- Search performance degradation
- Storage capacity warnings
- Error rate thresholds
- Video upload failures

## 6. Dependencies

### 6.1 System Dependencies
```bash
ffmpeg >= 4.4
opencv-python >= 4.8.0
python-ffmpeg >= 1.4
```

### 6.2 Python Dependencies
```requirements
ffmpeg-python==0.2.0
opencv-python==4.8.0
numpy>=1.21.0
scikit-learn>=1.0.2
```

## 7. Rollout Plan

### 7.1 Pre-deployment
- Set up staging environment
- Run performance tests
- Validate resource requirements
- Update documentation

### 7.2 Deployment
1. Database migrations
2. Backend service updates
3. Frontend deployment
4. Monitoring setup

### 7.3 Post-deployment
- Monitor error rates
- Track performance metrics
- Gather user feedback
- Plan optimizations
- Implement cleanup jobs for old or unused data when storage usage exceeds thresholds

## 8. Potential Challenges and Mitigations

### 8.1 Performance
- **Challenge**: Processing large videos
- **Mitigation**: Implement frame sampling, keyframe extraction, and parallel processing. Enforce strict limits on duration, size, and number of frames.

### 8.2 Storage
- **Challenge**: Increased storage requirements
- **Mitigation**: Only store keyframes/sampled frames. Implement cleanup jobs and storage optimization. Enforce per-video limits.

### 8.3 Search Accuracy
- **Challenge**: False positives in frame matching
- **Mitigation**: Tune similarity thresholds, require multiple frame matches, and implement verification steps.

### 8.4 Resource Usage
- **Challenge**: High CPU/memory usage during video processing
- **Mitigation**: Implement queue system, resource limits, and concurrent processing caps.

### 8.5 Security
- **Challenge**: Malicious uploads or attacks via video files
- **Mitigation**: Validate file types, scan for malware, limit upload size, and sanitize inputs.

### 8.6 Backward Compatibility
- **Challenge**: Breaking existing image search or data
- **Mitigation**: Ensure all migrations are backward compatible and image search is unaffected.

## 9. Success Metrics

- Video processing success rate > 95%
- Search accuracy > 90%
- Average processing time < 2 minutes for 5-minute videos
- Search response time < 2 seconds
- Storage efficiency (compression ratio > 10:1)
- User satisfaction metrics

## 10. Future Improvements

- GPU acceleration for feature extraction
- Advanced video fingerprinting
- Audio fingerprinting
- Machine learning-based similarity detection
- Automated content moderation
- Advanced video analytics
