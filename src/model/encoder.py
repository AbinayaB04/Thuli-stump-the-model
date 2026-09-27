import os
os.environ['USE_TF'] = '0'
os.environ['USE_TORCH'] = '1'

import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np


class ImageEncoder:

    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading {model_name} on {self.device}...")
        
        # Load the pretrained CLIP model and processor
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        
        # Set model to evaluation mode
        self.model.eval()

    def encode(self, image_path: str) -> np.ndarray:
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"Error loading image '{image_path}': {e}")
            return None

        with torch.no_grad():
            # Convert image into CLIP input format
            inputs = self.processor(
                images=image,
                return_tensors="pt"
            )
            
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get the image representation from CLIP's vision encoder
            vision_outputs = self.model.vision_model(
                pixel_values=inputs["pixel_values"]
            )

            # Take the pooled image representation
            pooled_output = vision_outputs.pooler_output

            # Project it into CLIP's final embedding space
            image_features = self.model.visual_projection(
                pooled_output
            )

            # L2 normalize the embedding
            image_features = torch.nn.functional.normalize(
                image_features,
                p=2,
                dim=-1
            )

        return image_features.cpu().numpy()