from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from rep0st.db import Base

class FrameInfo(Base):
    __tablename__ = 'frame_info'
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.id', ondelete='CASCADE'), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    is_keyframe = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

    post = relationship('Post', back_populates='frame_infos')
    feature_vectors = relationship('FeatureVector', back_populates='frame_info')

    def __repr__(self):
        return f"FrameInfo(id={self.id}, post_id={self.post_id}, frame_number={self.frame_number}, timestamp={self.timestamp})"