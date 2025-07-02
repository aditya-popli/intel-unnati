import platform
import requests
from pathlib import Path
import openvino_genai as ov_genai
from PIL import Image
from tqdm import tqdm
import sys

print("🔧 Initializing environment and checking helper scripts...")

# Download helper files if not present
if not Path("notebook_utils.py").exists():
    print("📥 Downloading notebook_utils.py...")
    r = requests.get("https://raw.githubusercontent.com/openvinotoolkit/openvino_notebooks/latest/utils/notebook_utils.py")
    open("notebook_utils.py", "w").write(r.text)

if not Path("cmd_helper.py").exists():
    print("📥 Downloading cmd_helper.py...")
    r = requests.get("https://raw.githubusercontent.com/openvinotoolkit/openvino_notebooks/latest/utils/cmd_helper.py")
    open("cmd_helper.py", "w").write(r.text)

print("✅ Helper files ready.")

# Import helpers and collect telemetry
from notebook_utils import collect_telemetry
from cmd_helper import optimum_cli

print("📊 Collecting telemetry...")
collect_telemetry("text-to-image-genai.py")

# Export the model using Optimum CLI with FP16 optimization
model_dir = Path("dreamlike_anime_1_0_ov")
if not model_dir.exists():
    print("📦 Exporting 'dreamlike-art/dreamlike-anime-1.0' to OpenVINO IR format (fp16)...")
    optimum_cli("dreamlike-art/dreamlike-anime-1.0", model_dir, extra_args=["--weight-format", "fp16"])
else:
    print("✅ Model already exported at:", model_dir)

# Use AUTO device so OpenVINO picks the best backend (CPU/GPU/NPU)
device = "AUTO"
print(f"🖥️ Using device: {device}")

# Create deterministic generator
random_generator = ov_genai.TorchGenerator(42)
print("🎲 Torch-compatible random generator created.")

# Load pipeline (use static image shape for best performance)
print("🚀 Initializing Text2ImagePipeline...")
if device != "NPU":
    pipe = ov_genai.Text2ImagePipeline(model_dir, device)
else:
    pipe = ov_genai.Text2ImagePipeline(model_dir)
    width, height = 512, 512
    pipe.reshape(1, width, height, pipe.get_generation_config().guidance_scale)
    pipe.compile(device)
print("✅ Pipeline is ready.")

# Define prompt
prompt = "Photosynthesis"
num_inference_steps = 10  # Reduced for faster inference
print(f"📸 Generating image for prompt: '{prompt}'")
print(f"🔄 Running {num_inference_steps} inference steps...")

# Progress bar for inference
pbar = tqdm(total=num_inference_steps)

def callback(step, num_steps, latent):
    pbar.update(1)
    sys.stdout.flush()
    return False

# Run generation
image_tensor = pipe.generate(
    prompt,
    width=512,
    height=512,
    num_inference_steps=num_inference_steps,
    num_images_per_prompt=1,
    generator=random_generator,
    callback=callback
)

pbar.close()

# Save and show the result
print("💾 Saving generated image to 'output_image.png'")
image = Image.fromarray(image_tensor.data[0])
image.save("output_image.png")
print("✅ Image saved successfully.")
# Optional: remove if running in non-GUI environment
print("🖼️ Opening image...")
image.show()
print("✅ Generation complete.")
