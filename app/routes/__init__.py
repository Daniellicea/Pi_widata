from flask import Blueprint, request, send_file
import io
from app.services.huggingface import generar_imagen

api = Blueprint('api', __name__)

@api.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt")

    imagen = generar_imagen(prompt)

    return send_file(
        io.BytesIO(imagen),
        mimetype='image/png'
    )