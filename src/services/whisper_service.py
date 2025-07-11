from flask import Flask, request, jsonify
import whisper
import torch
import gc
import threading
import time
import os
import tempfile
import subprocess
import logging

app = Flask(__name__)

# 设置日志
os.makedirs('log', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/whisper-log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhisperModelManager:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = "./whisper/large-v3.pt"
        self.lock = threading.Lock()
        
        # 优化设置
        if self.device == "cuda":
            torch.cuda.set_per_process_memory_fraction(0.6)
            torch.backends.cudnn.benchmark = True
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
        
    def get_model(self):
        with self.lock:
            if self.model is None:
                self._load_model()
            return self.model
            
    def _load_model(self):
        logger.info(f"加载模型到 {self.device}")
        
        if self.model:
            del self.model
            self.model = None
            
        if self.device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()
        
        # 加载模型
        if os.path.exists(self.model_path):
            self.model = whisper.load_model(self.model_path, device=self.device)
        else:
            self.model = whisper.load_model("large-v3", device=self.device)
            
        # 优化设置
        self.model.eval()
        for param in self.model.parameters():
            param.requires_grad = False
            
        if self.device == "cuda":
            torch.cuda.empty_cache()
            memory = torch.cuda.memory_allocated() / 1024**3
            logger.info(f"模型加载完成，显存使用: {memory:.2f}GB")
        else:
            logger.info("模型加载完成")
            
    def transcribe(self, audio_path):
        model = self.get_model()
        
        options = {
            "beam_size": 1,
            "best_of": 1,
            "temperature": 0.0,
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6,
            "condition_on_previous_text": False,
            "verbose": False
        }
        
        if self.device == "cuda":
            torch.cuda.empty_cache()
            
        with torch.no_grad():
            result = model.transcribe(audio_path, **options)
            
        if self.device == "cuda":
            torch.cuda.empty_cache()
            
        return result

model_manager = WhisperModelManager()

def extract_audio_from_video(video_path):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        audio_path = temp_audio.name
        
    cmd = [
        "ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", 
        "-ar", "16000", "-ac", "1", "-threads", "2", "-f", "wav", 
        audio_path, "-y"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd)
        return audio_path
    except Exception as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise Exception(f"音频提取失败: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    try:
        with model_manager.lock:
            model_loaded = model_manager.model is not None
            
        memory_info = {}
        if torch.cuda.is_available():
            memory_info = {
                "allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                "reserved_gb": torch.cuda.memory_reserved() / 1024**3,
                "device_name": torch.cuda.get_device_name()
            }
            
        return jsonify({
            "status": "healthy",
            "model_loaded": model_loaded,
            "device": model_manager.device,
            "memory_info": memory_info
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe_endpoint():
    try:
        if not request.json or 'audio_path' not in request.json:
            return jsonify({"error": "缺少audio_path参数"}), 400
            
        audio_path = request.json['audio_path']
        if not os.path.exists(audio_path):
            return jsonify({"error": f"音频文件不存在: {audio_path}"}), 400
            
        start_time = time.time()
        result = model_manager.transcribe(audio_path)
        processing_time = time.time() - start_time
        
        return jsonify({
            "success": True,
            "segments": result['segments'],
            "text": result['text'],
            "language": result['language'],
            "processing_time": processing_time
        })
        
    except Exception as e:
        logger.error(f"转录错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/transcribe_video', methods=['POST'])
def transcribe_video_endpoint():
    try:
        if not request.json or 'video_path' not in request.json:
            return jsonify({"error": "缺少video_path参数"}), 400
            
        video_path = request.json['video_path']
        if not os.path.exists(video_path):
            return jsonify({"error": f"视频文件不存在: {video_path}"}), 400
            
        start_time = time.time()
        audio_path = extract_audio_from_video(video_path)
        
        try:
            result = model_manager.transcribe(audio_path)
            processing_time = time.time() - start_time
            
            return jsonify({
                "success": True,
                "segments": result['segments'],
                "text": result['text'],
                "language": result['language'],
                "processing_time": processing_time
            })
            
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
    except Exception as e:
        logger.error(f"视频转录错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/model/reload', methods=['POST'])
def reload_model():
    try:
        with model_manager.lock:
            model_manager._load_model()
        return jsonify({"success": True, "message": "模型重新加载完成"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/model/unload', methods=['POST'])
def unload_model():
    try:
        with model_manager.lock:
            if model_manager.model:
                del model_manager.model
                model_manager.model = None
                
            if model_manager.device == "cuda":
                torch.cuda.empty_cache()
            gc.collect()
            
        return jsonify({"success": True, "message": "模型已卸载"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/memory/optimize', methods=['POST'])
def optimize_memory():
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
            
            return jsonify({
                "success": True,
                "message": "显存优化完成",
                "allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                "reserved_gb": torch.cuda.memory_reserved() / 1024**3
            })
        else:
            return jsonify({"success": False, "error": "CUDA不可用"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    logger.info("启动Whisper服务")
    
    # 环境变量优化
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
    
    # 预加载模型
    try:
        model_manager.get_model()
        logger.info("模型预加载完成")
    except Exception as e:
        logger.error(f"模型预加载失败: {e}")
        
    app.run(host="127.0.0.1", port=5001, debug=False, threaded=True)