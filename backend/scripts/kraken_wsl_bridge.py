import sys
import json
import os
import traceback

def configure_torch_runtime():
    try:
        import torch

        if hasattr(torch, "set_float32_matmul_precision"):
            torch.set_float32_matmul_precision("high")
        if hasattr(torch.backends, "cudnn"):
            torch.backends.cudnn.benchmark = True
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return torch, device
    except Exception:
        return None, "cpu"

def run_kraken(payload_path):
    # Read payload
    with open(payload_path, 'r', encoding='utf-8-sig') as f:
        payload = json.load(f)
        
    image_path = payload['image_path']
    model_path = payload['model_path']
    boxes = payload['boxes']
    
    response = {
        'status': 'error',
        'lines': [],
        'error_message': '',
        'device': 'unknown',
        'cuda_available': False,
        'cuda_device_name': None
    }
    
    try:
        torch, device = configure_torch_runtime()
        response['device'] = device
        if torch is not None:
            response['cuda_available'] = bool(torch.cuda.is_available())
            response['cuda_device_name'] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None

        from kraken.tasks import RecognitionTaskModel
        from kraken.configs import RecognitionInferenceConfig
        from kraken.containers import Segmentation, BBoxLine
        from PIL import Image
        
        # Load image
        img = Image.open(image_path).convert('RGB')
        
        # Prepare segmentation container
        lines = []
        for box_id, box_coords in boxes.items():
            # box_coords: [x1, y1, x2, y2]
            bl = BBoxLine(id=str(box_id), bbox=box_coords)
            lines.append(bl)
            
        seg = Segmentation(type="bbox", lines=lines, text_direction="horizontal-rl", imagename=image_path, script_detection=False)
        
        from kraken.lib.models import load_any
        from kraken.rpred import rpred
        
        # Load model
        model = load_any(model_path)
        if device == "cuda" and hasattr(model, "to"):
            moved_model = model.to("cuda")
            if moved_model is not None:
                model = moved_model
        if hasattr(model, "eval"):
            model.eval()
        
        # Run inference
        if torch is not None and hasattr(torch, "inference_mode"):
            with torch.inference_mode():
                records = list(rpred(network=model, im=img, bounds=seg))
        else:
            records = list(rpred(network=model, im=img, bounds=seg))
        
        # Serialize results
        output_lines = []
        for i, rline in enumerate(records):
            output_lines.append({
                'id': str(i),
                'text': rline.prediction,
                'confidence': float(sum(rline.confidences)/len(rline.confidences)) if hasattr(rline, 'confidences') and rline.confidences else 0.0
            })
            
        response['status'] = 'success'
        response['lines'] = output_lines
        
    except Exception as e:
        response['error_message'] = str(e)
        response['traceback'] = traceback.format_exc()
        
    # Write response
    response_path = payload_path + '.out.json'
    with open(response_path, 'w', encoding='utf-8') as f:
        json.dump(response, f, ensure_ascii=False)
        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python kraken_wsl_bridge.py <payload_path>")
        sys.exit(1)
        
    run_kraken(sys.argv[1])
