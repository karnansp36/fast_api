# download_model.py
from transformers import pipeline
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_distilbert_emotion():
    """Download and save the DistilBERT emotion model"""
    model_dir = os.path.join("app", "models", "emotion_model")
    os.makedirs(model_dir, exist_ok=True)
    
    model_name = "bhadresh-savani/distilbert-base-uncased-emotion"
    
    logger.info(f"🚀 Downloading {model_name}...")
    logger.info("This is the best balanced model: ~250MB, fast, and accurate")
    logger.info("Emotions: sadness, joy, love, anger, fear, surprise")
    
    try:
        # Download the model
        classifier = pipeline(
            "text-classification",
            model=model_name,
            return_all_scores=True
        )
        
        # Save to local directory
        classifier.save_pretrained(model_dir)
        
        logger.info(f"✅ Model successfully downloaded and saved to: {model_dir}")
        logger.info("📁 Files created:")
        
        for file in os.listdir(model_dir):
            file_path = os.path.join(model_dir, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            logger.info(f"  - {file} ({size_mb:.1f} MB)")
        
        # Test the model
        test_texts = [
            "I am so happy and excited today!",
            "This makes me very angry and frustrated",
            "I feel scared and anxious about what might happen"
        ]
        
        logger.info("🧪 Testing the model:")
        for text in test_texts:
            result = classifier(text)
            primary_emotion = max(result[0], key=lambda x: x['score'])
            logger.info(f"  '{text}' → {primary_emotion['label']} ({primary_emotion['score']:.2f})")
            
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        logger.info("💡 Make sure you have internet connection")
        logger.info("💡 If behind proxy, set HTTP_PROXY/HTTPS_PROXY environment variables")

if __name__ == "__main__":
    download_distilbert_emotion()