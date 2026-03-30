import os
from transformers import logging
from app import create_app
from diffusers import StableDiffusionPipeline

# Configurar Hugging Face Token
os.environ["HF_TOKEN"] = "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"

# Silenciar logs de Transformers
logging.set_verbosity_error()  # Solo mostrar errores importantes

# Inicializar Flask
app = create_app()

# Inicializar Stable Diffusion solo si se necesita
# Esto evita que se cargue en memoria si no se usa inmediatamente
pipe = None
def get_pipeline():
    global pipe
    if pipe is None:
        pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
        pipe.to("cpu")  # o "cuda" si tienes GPU en local
    return pipe

# Ejecutar Flask en desarrollo
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)