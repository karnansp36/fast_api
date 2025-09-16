# services/emotion_service.py
import os
import logging
from typing import Dict, Any
from transformers import pipeline

logger = logging.getLogger(__name__)

class EmotionService:
    def __init__(self):
        self.classifier = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the emotion model with fallback options"""
        # Path where you can bundle a local copy of the model
        local_model_path = os.path.join("app", "models", "emotion_model")

        try:
            if os.path.exists(local_model_path):
                # Load from local packaged model
                logger.info(f"Loading emotion model from local path: {local_model_path}")
                self.classifier = pipeline(
                    "text-classification",
                    model=local_model_path,
                    return_all_scores=True
                )
            else:
                # Try Hugging Face download
                logger.info("Local model not found. Trying Hugging Face...")
                self.classifier = pipeline(
                    "text-classification",
                    model="j-hartmann/emotion-english-distilroberta-base",
                    return_all_scores=True
                )
            logger.info("Emotion model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load emotion model: {e}")
            self.classifier = None

    def detect_emotion(self, text: str) -> Dict[str, Any]:
        """Detect emotion from text with fallback"""
        if not self.classifier or not text.strip():
            return {"emotion": "neutral", "confidence": 0.0, "all_emotions": {}}

        try:
            results = self.classifier(text[:512])  # Limit text length
            if results and len(results) > 0:
                emotions = results[0]
                # Get the emotion with highest score
                primary_emotion = max(emotions, key=lambda x: x['score'])

                # Format all emotions for context
                all_emotions = {e['label']: float(e['score']) for e in emotions}

                return {
                    "emotion": primary_emotion['label'],
                    "confidence": float(primary_emotion['score']),
                    "all_emotions": all_emotions
                }
        except Exception as e:
            logger.error(f"Emotion detection failed: {e}")

        return {"emotion": "neutral", "confidence": 0.0, "all_emotions": {}}


# Global instance
emotion_service = EmotionService()
