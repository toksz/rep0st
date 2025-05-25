# Detailed Plan for Video Integration in rep0st

This document outlines a comprehensive plan for integrating video support into rep0st's reverse search functionality, building upon the initial `docs/video_integration_plan.md` and incorporating insights from the existing codebase and deployment configurations.

## Phase 0: Initial Setup & Environment Preparation

1.  **Review Existing Environment**:
    *   `ffmpeg` is confirmed to be correctly installed and accessible within the Docker environment, as seen in [`deployment/rep0st.Dockerfile`](deployment/rep0st.Dockerfile).
    *   `paradedb` (PostgreSQL with `pgvector`) is confirmed as the database in use, indicated by [`deployment/postgresql.Dockerfile`](deployment/postgresql.Dockerfile) and the `feature_vector_post_type_video_vec_approx` index in the plan.

2.  **Dependency Management**:
    *   Add `opencv-python`, `ffmpeg-python`, `numpy`, and `scikit-learn` to `Pipfile` and `requirements.txt` (if applicable) for Python dependencies.
    *   Ensure these Python dependencies are installed via `pipenv` during the Docker build process.

## Phase 1: Core System Updates

### 1.1 Database Changes

*   **Schema Implementation**:
    *   Create a new ORM model, `FrameInfo`, in a new file (e.g., [`rep0st/db/frame_info.py`](rep0st/db/frame_info.py)) to represent the `frame_info` table. This model will include fields for `id`, `post_id`, `frame_number`, `timestamp`, `is_keyframe`, and `created_at`.
    *   Modify the existing `FeatureVector` ORM model in [`rep0st/db/feature.py`](rep0st/db/feature.py) to include `frame_number` (Integer) and `frame_info_id` (Integer, ForeignKey to `frame_info.id`).
    *   Update the `Post` ORM model in [`rep0st/db/post.py`](rep0st/db/post.py) if necessary to reflect the new relationships, specifically how `feature_vectors` might now relate to `frame_info` through `FeatureVector`.
    *   Implement database migration scripts to apply these schema changes.

*   **Indexing**:
    *   Ensure the proposed indices (`idx_frame_info_post_id`, `idx_frame_info_post_id_frame_number`, `idx_frame_info_post_id_timestamp`, `idx_feature_vector_frame_info`, `feature_vector_post_type_video_vec_approx`) are correctly defined and applied. The `feature_vector_post_type_video_vec_approx` index is crucial for efficient video similarity search.

### 1.2 Configuration Updates

*   **Centralized Configuration**: Create a new Python configuration file, e.g., [`rep0st/config/rep0st_video_config.py`](rep0st/config/rep0st_video_config.py), to house all video-related flags. This promotes modularity and easier management.
*   **Define Flags**: Implement the following flags using `flags.DEFINE_integer` and `flags.DEFINE_float`:
    *   `rep0st_video_keyframe_interval`
    *   `rep0st_video_max_keyframes`
    *   `rep0st_video_max_duration`
    *   `rep0st_video_frame_batch_size`
    *   `rep0st_video_max_upload_size_mb`
    *   `rep0st_video_min_matches`
    *   `rep0st_video_similarity_threshold`
*   **Integration**: Ensure these flags are accessible and used by the relevant services (`media_service`, `feature_service`, `post_search_service`).

## Phase 2: Component Updates

### 2.1 Media Service Enhancements ([`rep0st/service/media_service.py`](rep0st/service/media_service.py))

*   **Video Processing**:
    *   Implement functions for video frame extraction using `ffmpeg-python` and `OpenCV`.
    *   Add logic for keyframe detection and intelligent frame sampling based on configured intervals and limits.
    *   Integrate video format validation and enforce `rep0st_video_max_upload_size_mb` and `rep0st_video_max_duration`.
    *   Implement frame batching for efficient processing.
    *   Add robust error handling for video decoding and processing failures.
    *   Implement security measures: file type validation, potential malware scanning (if external tool integration is planned), and input sanitization.
    *   Develop fallback mechanisms for unsupported codecs or corrupt video files.

### 2.2 Feature Service Updates ([`rep0st/service/feature_service.py`](rep0st/service/feature_service.py))

*   **Video Feature Extraction**:
    *   Extend the existing feature extraction pipeline to process video frames. Reuse the image feature extraction logic for individual frames.
    *   Implement parallel processing and batching of frames for feature generation.
    *   Store extracted frame metadata (frame number, timestamp, keyframe flag) in the new `frame_info` table and link the generated feature vectors to `frame_info_id`.
    *   Implement progress tracking for long-running video processing tasks.
    *   Enforce `rep0st_video_max_keyframes` and other limits, stopping processing and logging warnings when limits are reached.

### 2.3 Search Service Modifications ([`rep0st/service/post_search_service.py`](rep0st/service/post_search_service.py))

*   **Video Similarity Search**:
    *   Develop a new search logic that queries all frames of a video.
    *   Implement frame matching and temporal alignment algorithms to group nearby matches and identify video similarity.
    *   Aggregate results by video and calculate a match confidence score based on `rep0st_video_min_matches` and `rep0st_video_similarity_threshold`.
    *   Optimize search performance by limiting the number of candidate matches.
    *   Ensure backward compatibility so that existing image search functionality remains unaffected.
    *   Rank video search results based on the number of matching frames and their temporal alignment.

### 2.4 API and Frontend Updates ([`rep0st/web/api/`](rep0st/web/api/) and [`rep0st/web/frontend/`](rep0st/web/frontend/))

*   **API Endpoints**:
    *   Add new API endpoints for video upload, processing status, and video similarity search.
    *   Implement input validation for video uploads (file type, size, duration).
    *   Integrate progress reporting for video processing.
    *   Ensure proper error handling and clear error messages for API consumers.
    *   Consider implementing chunked and resumable uploads for large video files.

*   **Frontend UI**:
    *   Update the user interface to support video uploads, including drag-and-drop functionality and file selection.
    *   Display progress indicators during video upload and processing.
    *   Implement video preview functionality.
    *   Design and implement a results visualization that shows frame-level matches with timestamp markers for video search results.
    *   Provide clear and user-friendly error messages for upload and processing failures.
    *   Implement client-side security measures, such as input sanitization and limiting concurrent uploads.

## Phase 3: Implementation Phases (Detailed Breakdown)

This section from the [`docs/video_integration_plan.md`](docs/video_integration_plan.md) is already well-defined and provides a good timeline.

## Phase 4: Testing Strategy

*   **Unit Tests**: Develop comprehensive unit tests for all new and modified components, including:
    *   Video frame extraction and validation logic.
    *   Feature vector generation for individual frames.
    *   Frame matching algorithms and temporal alignment.
    *   Result aggregation and similarity scoring.
    *   Database ORM model interactions (`FrameInfo`, `FeatureVector` updates).
*   **Integration Tests**: Implement end-to-end integration tests covering:
    *   Full video processing pipeline (upload -> frame extraction -> feature generation -> indexing).
    *   Video similarity search functionality, including edge cases (e.g., very short/long videos, videos with no matches).
    *   Combined image and video search scenarios.
    *   Database migrations and data integrity.
    *   API endpoint functionality and error handling.
*   **Performance Tests**:
    *   Define specific performance metrics: processing time per frame, search response time, memory usage during batch processing.
    *   Create test cases for large video processing, concurrent video uploads, and high-load search scenarios.
    *   Focus on optimizing database queries and indices based on performance test results.
*   **Edge Case Testing**: Add specific test cases for scenarios like:
    *   Corrupt video files.
    *   Videos with unusual aspect ratios or resolutions.
    *   Videos with very few or very many keyframes.
    *   Empty video uploads.

## Phase 5: Monitoring and Maintenance

*   **New Metrics**: Implement tracking for all proposed metrics: video upload success rate, processing time per frame, feature generation speed, search response times, storage usage, error rates, cache hit rates.
*   **Alerts**: Configure alerts for critical issues such as video processing failures, search performance degradation, storage capacity warnings, and elevated error rates.
*   **Cleanup Jobs**: Implement automated cleanup jobs for old or unused video data and feature vectors to manage storage growth, especially when storage usage exceeds predefined thresholds.

## Phase 6: Dependencies

*   **System Dependencies**: Confirm `ffmpeg` is installed in the Docker image ([`deployment/rep0st.Dockerfile`](deployment/rep0st.Dockerfile)).
*   **Python Dependencies**: Explicitly add `ffmpeg-python`, `opencv-python`, `numpy`, and `scikit-learn` to the `Pipfile` and ensure they are installed during the Docker build process.

## Phase 7: Rollout Plan

This section from the [`docs/video_integration_plan.md`](docs/video_integration_plan.md) is already well-defined.

## Phase 8: Potential Challenges and Mitigations

This section from the [`docs/video_integration_plan.md`](docs/video_integration_plan.md) is already well-defined and provides excellent foresight.

## Phase 9: Success Metrics

This section from the [`docs/video_integration_plan.md`](docs/video_integration_plan.md) is already well-defined.

## Phase 10: Future Improvements

This section from the [`docs/video_integration_plan.md`](docs/video_integration_plan.md) is already well-defined.

---

Here's a Mermaid diagram illustrating the high-level data flow for video integration:

```mermaid
graph TD
    A[User Uploads Video] --> B(Frontend API)
    B --> C{Media Service}
    C --> D[Video Frame Extraction]
    D --> E[Frame Metadata]
    D --> F[Individual Frames]
    F --> G{Feature Service}
    G --> H[Feature Vector Generation]
    H --> I[Store Feature Vectors in DB]
    E --> J[Store Frame Metadata in DB]
    I & J --> K[PostgreSQL Database]
    L[User Initiates Video Search] --> M(Frontend API)
    M --> N{Search Service}
    N --> O[Query Feature Vectors in DB]
    O --> P[Aggregate Matches by Video]
    P --> Q[Rank Results]
    Q --> R[Display Results on Frontend]
    K --> O