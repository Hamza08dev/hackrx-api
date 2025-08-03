# Performance Optimization Guide

## Why Was Chunking Taking So Long?

The chunking process was slow due to several performance bottlenecks:

### 1. **Sequential API Calls**
- Each chunk required a separate API call to Gemini's embedding service
- 200ms delay between each API call
- For 20 chunks: 20 API calls × (API time + 200ms delay) = 4+ seconds just in delays

### 2. **Inefficient Chunking Strategy**
- Small chunk size (800 chars) created too many chunks
- High overlap (150 chars) meant redundant processing
- More chunks = more API calls = slower processing

### 3. **No Parallel Processing**
- All operations were sequential
- No batching or concurrent processing
- Single-threaded API calls

## Optimizations Implemented

### 1. **Parallel Batch Processing**
```python
# Before: Sequential processing
for chunk in chunks:
    embedding = create_embedding(chunk)
    time.sleep(0.2)  # 200ms delay

# After: Parallel batch processing
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(create_embedding, chunk) for chunk in batch]
    # Process 3 chunks simultaneously
```

### 2. **Optimized Chunking Parameters**
```python
# Before
chunk_size = 800      # Too small
chunk_overlap = 150   # Too much overlap

# After
chunk_size = 1500     # Larger chunks = fewer API calls
chunk_overlap = 100   # Reduced overlap
min_chunk_size = 100  # Filter out tiny chunks
```

### 3. **Reduced Rate Limiting Delays**
```python
# Before
retry_delay = 1.0     # 1 second delays
batch_delay = 0.5     # 500ms between chunks

# After
retry_delay = 0.5     # 500ms delays
batch_delay = 0.1     # 100ms between batches
```

### 4. **Configurable Performance Profiles**
```python
# Fast profile (speed over quality)
"fast": {
    "chunk_size": 2000,
    "batch_size": 8,
    "max_workers": 5,
    "batch_delay": 0.05
}

# Balanced profile (default)
"balanced": {
    "chunk_size": 1500,
    "batch_size": 5,
    "max_workers": 3,
    "batch_delay": 0.1
}

# Quality profile (quality over speed)
"quality": {
    "chunk_size": 1000,
    "batch_size": 3,
    "max_workers": 2,
    "batch_delay": 0.2
}
```

## Performance Improvements

### Expected Speed Improvements:
- **Chunking**: 2-3x faster (fewer, larger chunks)
- **Embedding**: 3-5x faster (parallel processing + batching)
- **Overall**: 2-4x faster total processing time

### For a 10,000 character document:
- **Before**: ~12-15 chunks × (1s API + 0.2s delay) = 15-20 seconds
- **After**: ~6-8 chunks × (1s API + 0.1s delay) = 6-8 seconds

## How to Use the Optimizations

### 1. **Environment Variables**
```bash
# Set performance profile
export CHUNK_SIZE=1500
export BATCH_SIZE=5
export MAX_WORKERS=3

# Or use fast profile
export CHUNK_SIZE=2000
export BATCH_SIZE=8
export MAX_WORKERS=5
```

### 2. **Code Configuration**
```python
from config import Config

# Use fast profile
config = Config.get_embedding_config("fast")
embedder = TextEmbedder(config=config)

# Use custom configuration
config = {
    "chunk_size": 2000,
    "batch_size": 8,
    "max_workers": 5
}
embedder = TextEmbedder(config=config)
```

### 3. **Testing Performance**
```bash
# Run performance test
python performance_test.py

# Run quick optimization test
python test_optimizations.py

# Check current configuration
python config.py
```

## Monitoring and Debugging

### 1. **Performance Metrics**
The system now logs detailed performance metrics:
```
✅ Created 6 chunks from 15000 chars (OPTIMIZED)
🧠 Processing batch 1-5/6
✅ Successfully embedded 6/6 chunks (BATCHED)
🎯 Complete: 6 chunks with embeddings (OPTIMIZED)
```

### 2. **Configuration Inspection**
```python
from config import Config
Config.print_current_config()
```

### 3. **Performance Profiles**
- **Fast**: Maximum speed, larger chunks, more parallel workers
- **Balanced**: Good balance of speed and quality (default)
- **Quality**: Maximum quality, smaller chunks, fewer parallel workers

## Troubleshooting

### If Still Slow:
1. **Check API Rate Limits**: Ensure you're not hitting Gemini API limits
2. **Increase Chunk Size**: Try `CHUNK_SIZE=2000` for fewer API calls
3. **Increase Parallel Workers**: Try `MAX_WORKERS=5` for more concurrent calls
4. **Reduce Delays**: Try `BATCH_DELAY=0.05` for faster processing

### If Quality Issues:
1. **Decrease Chunk Size**: Try `CHUNK_SIZE=1000` for better context
2. **Increase Overlap**: Try `CHUNK_OVERLAP=150` for better continuity
3. **Use Quality Profile**: Switch to quality-focused settings

## Best Practices

1. **Start with Balanced Profile**: Default settings work well for most cases
2. **Monitor API Usage**: Watch for rate limiting errors
3. **Test with Your Data**: Different document types may need different settings
4. **Scale Gradually**: Increase parallel workers slowly to avoid overwhelming APIs

## Files Modified

- `processing/embedder.py`: Main optimization implementation
- `processing/entity_extractor.py`: Reduced delays
- `config.py`: Centralized configuration management
- `performance_test.py`: Performance testing utilities
- `test_optimizations.py`: Quick optimization demonstration

These optimizations should significantly improve your chunking performance while maintaining quality! 