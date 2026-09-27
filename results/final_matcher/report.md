# Final Matcher Validation Report

- **Final Catalogue Size**: 5144
- **Model**: openai/clip-vit-base-patch32
- **Embedding Dimension**: 512
- **FAISS Index Type**: IndexFlatIP
- **Top-5 Retrieval Behavior**: Returns 5 unique items based on Inner Product (Cosine Similarity) over L2 normalized vectors.

## Latency Statistics (ms)
- **Average Query Encoding Time**: 278.46 ms
- **Median Query Encoding Time**: 257.69 ms
- **Average FAISS Search Time**: 7.15 ms
- **Median FAISS Search Time**: 2.11 ms
- **Average Total Query Latency**: 285.61 ms

## Accuracy Note
> **IMPORTANT**: The 7-query results below are NOT accuracy measurements because verified ground truth is unavailable. This is an end-to-end functionality validation, not an accuracy evaluation.
