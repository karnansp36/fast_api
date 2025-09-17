# services/emotion_service.py
import os
import logging
from typing import Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

logger = logging.getLogger(__name__)

class EmotionService:
    def __init__(self):
        self.classifier = None
        self.model_loaded = False
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the emotion model from local files only"""
        local_model_path = os.path.join("app", "models", "emotion_model")
        
        # Check if model files exist - accept both .bin and .safetensors
        required_files = ['config.json', 'vocab.txt']
        model_files = ['pytorch_model.bin', 'model.safetensors']  # Either is acceptable
        
        if not os.path.exists(local_model_path):
            logger.error(f"Model directory not found: {local_model_path}")
            self._create_fallback_service()
            return
            
        available_files = os.listdir(local_model_path)
        logger.info(f"Found files: {available_files}")
        
        # Check for required files
        missing_required = [f for f in required_files if f not in available_files]
        if missing_required:
            logger.error(f"Missing required files: {missing_required}")
            self._create_fallback_service()
            return
            
        # Check if we have at least one model file
        has_model_file = any(model_file in available_files for model_file in model_files)
        if not has_model_file:
            logger.error(f"Missing model file. Need one of: {model_files}")
            self._create_fallback_service()
            return

        try:
            logger.info("Loading emotion model from local files...")
            
            # Load components separately
            tokenizer = AutoTokenizer.from_pretrained(local_model_path)
            model = AutoModelForSequenceClassification.from_pretrained(local_model_path)
            
            # Create pipeline with loaded components
            self.classifier = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                top_k=None,  # Use this instead of return_all_scores=True
                device=0 if torch.cuda.is_available() else -1
            )
            
            self.model_loaded = True
            logger.info("✅ Emotion model loaded successfully from local files")
            
            # Test the model
            self._test_model()
            
        except Exception as e:
            logger.error(f"❌ Failed to load local model: {e}")
            self._create_fallback_service()

    def _test_model(self):
        """Test if the model works correctly"""
        try:
            test_result = self.classifier("I am happy")
            if test_result and len(test_result) > 0:
                primary = max(test_result[0], key=lambda x: x['score'])
                logger.info(f"✅ Model test passed: 'I am happy' → {primary['label']} ({primary['score']:.2f})")
            else:
                logger.warning("⚠️ Model test returned empty results")
        except Exception as e:
            logger.error(f"❌ Model test failed: {e}")

    def _create_fallback_service(self):
        """Create a fallback service if model loading fails"""
        logger.warning("⚠️ Using rule-based fallback emotion detection")
        self.model_loaded = True
        self.classifier = None

    def detect_emotion(self, text: str) -> Dict[str, Any]:
        """Detect emotion from text"""
        if not text.strip():
            return self._get_neutral_response()

        # Use transformer model if available
        if self.classifier and self.model_loaded:
            try:
                results = self.classifier(text[:512])
                if results and len(results) > 0:
                    emotions = results[0]
                    primary_emotion = max(emotions, key=lambda x: x['score'])

                    all_emotions = {e['label']: float(e['score']) for e in emotions}

                    return {
                        "emotion": primary_emotion['label'],
                        "confidence": float(primary_emotion['score']),
                        "all_emotions": all_emotions,
                        "model": "distilbert",
                        "success": True
                    }
            except Exception as e:
                logger.error(f"Model detection failed: {e}")

        # Fallback to rule-based detection
        return self._rule_based_emotion_detection(text)

    def _rule_based_emotion_detection(self, text: str) -> Dict[str, Any]:
        """Rule-based emotion detection fallback"""
        text_lower = text.lower()
        
        emotion_keywords = {
            'sadness': ['sad', 'unhappy', 'depressed', 'cry', 'tears', 'miss', 'lonely', 'heartbroken'],
            'joy': ['happy', 'joy', 'excited', 'great', 'wonderful', 'amazing', 'fantastic', 'good'],
            'love': ['love', 'adore', 'cherish', 'romantic', 'affection', 'care', 'sweet', 'darling'],
            'anger': ['angry', 'mad', 'furious', 'hate', 'annoyed', 'frustrated', 'outraged', 'upset'],
            'fear': ['scared', 'afraid', 'fear', 'anxious', 'worried', 'nervous', 'terrified', 'panic'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'wow', 'unexpected', 'astonishing']
        }
        
        scores = {emotion: 0.0 for emotion in emotion_keywords.keys()}
        scores['neutral'] = 0.1
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[emotion] += 0.3
        
        primary_emotion, confidence = max(scores.items(), key=lambda x: x[1])
        total = sum(scores.values())
        normalized_scores = {k: round(v/total, 3) for k, v in scores.items()}
        
        return {
            "emotion": primary_emotion,
            "confidence": min(0.9, confidence),
            "all_emotions": normalized_scores,
            "model": "rule_based",
            "success": False
        }

    def _get_neutral_response(self) -> Dict[str, Any]:
        """Return neutral response template"""
        return {
            "emotion": "neutral",
            "confidence": 0.0,
            "all_emotions": {emotion: 0.0 for emotion in ['sadness', 'joy', 'love', 'anger', 'fear', 'surprise']},
            "model": "fallback",
            "success": False
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_loaded": self.model_loaded,
            "model_type": "distilbert" if self.classifier else "rule_based",
            "using_fallback": self.classifier is None
        }


# Global instance
emotion_service = EmotionService()