import os
import time
import argparse
import numpy as np
import pandas as pd
import faiss
from pathlib import Path
from src.model.encoder import ImageEncoder

INDEX_PATH = Path("data/index/etsy_clip.index")
METADATA_PATH = Path("data/index/etsy_index_metadata.csv")

class BaselineMatcher:
    def __init__(self):
        print("Loading FAISS index...")
        self.index = faiss.read_index(str(INDEX_PATH))
        
        print("Loading metadata...")
        self.metadata = pd.read_csv(METADATA_PATH)
        
        print("Loading encoder...")
        self.encoder = ImageEncoder()
        
    def search(self, image_path: str, top_k: int = 5):
        t0 = time.time()
        emb = self.encoder.encode(image_path)
        t1 = time.time()
        encode_time = t1 - t0
        
        if emb is None:
            return None, 0, 0
            
        # FAISS search
        t2 = time.time()
        similarities, indices = self.index.search(emb, top_k * 3)  # Search for more to account for duplicates
        t3 = time.time()
        query_time = t3 - t2
        
        results = []
        seen_listings = set()
        
        for sim, faiss_id in zip(similarities[0], indices[0]):
            if faiss_id == -1:
                continue
                
            row = self.metadata.iloc[faiss_id]
            # Handle possible naming differences from metadata saving
            listing_id = str(row.get('listing_id') or row.get('item_id'))
            
            # Ensure unique listings
            if listing_id not in seen_listings:
                seen_listings.add(listing_id)
                results.append({
                    'listing_id': listing_id,
                    'title': row['title'],
                    'category': row['category'],
                    'similarity': float(sim),
                    'image_path': row['local_image_path']
                })
                
            if len(results) >= top_k:
                break
                
        return results, encode_time, query_time

def main():
    parser = argparse.ArgumentParser(description="Baseline Image Retrieval")
    parser.add_argument("--image", type=str, required=True, help="Path to query image")
    args = parser.parse_args()
    
    if not Path(args.image).exists():
        print(f"Error: Query image not found: {args.image}")
        return
        
    matcher = BaselineMatcher()
    results, enc_time, q_time = matcher.search(args.image, top_k=5)
    
    from src.rejection import OpenSetRejector, THRESHOLD_STATUS
    rejector = OpenSetRejector()
    decision = "NO_MATCH"
    if results:
        top1_sim = results[0]['similarity']
        decision = rejector.evaluate(top1_sim)
        
    print("\n" + "="*50)
    print("OPEN-SET REJECTION DECISION")
    print("="*50)
    print(f"Status: {THRESHOLD_STATUS} (Provisional/Uncalibrated)")
    print(f"Decision: {decision}")
    if results:
        print(f"Top-1 Similarity: {top1_sim:.4f}")
    
    print("\n" + "="*50)
    print("RETRIEVAL RESULTS")
    print("="*50)
    
    if not results:
        print("No results found or error encoding image.")
        return
        
    for i, res in enumerate(results, 1):
        print(f"Rank {i}")
        print(f"Product: {res['title']}")
        print(f"Category: {res['category']}")
        print(f"Listing ID: {res['listing_id']}")
        print(f"Image: {res['image_path']}")
        print(f"Similarity: {res['similarity']:.4f}")
        print("-" * 50)
        
    print(f"\nEncoding latency: {enc_time*1000:.2f} ms")
    print(f"FAISS search latency: {q_time*1000:.2f} ms")

if __name__ == "__main__":
    main()
