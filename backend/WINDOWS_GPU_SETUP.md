# Windows NVIDIA GPU Setup

If you're deploying on Windows with an NVIDIA GPU, follow these steps for maximum performance:

## 1. Install CUDA Toolkit
Download and install CUDA Toolkit 11.8 or 12.x from:
https://developer.nvidia.com/cuda-downloads

## 2. Install GPU-accelerated ONNX Runtime
After installing regular requirements, replace `onnxruntime` with GPU version:

```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

## 3. Verify GPU Detection
Run this test:

```bash
cd backend
python -c "from app.services.face_recognition import face_recognition; face_recognition.initialize()"
```

You should see:
```
✅ InsightFace buffalo_s loaded on CUDA GPU
```

## 4. Performance Expected
- **Mac (CoreML)**: ~100-150ms per frame
- **Windows CPU**: ~200-300ms per frame  
- **Windows NVIDIA GPU**: ~20-50ms per frame ⚡

## Troubleshooting

### If CUDA not detected:
1. Check NVIDIA drivers are installed: `nvidia-smi`
2. Verify CUDA version matches onnxruntime-gpu requirements
3. Check providers list in logs

### If memory errors:
Reduce detection size in `face_recognition.py`:
```python
self.model.prepare(
    ctx_id=0,
    det_size=(320, 320)  # Lower = less memory, faster but less accurate
)
```

## Provider Priority
The system automatically tries providers in this order:
1. **CUDAExecutionProvider** (Windows NVIDIA GPU)
2. **CoreMLExecutionProvider** (Mac Apple Silicon)
3. **CPUExecutionProvider** (Fallback)

First available provider is used.
