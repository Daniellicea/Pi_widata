import os
import re
import torch
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.financial import Credito, Gasto, Institucion, CategoriaGasto
from app.forms import CreditoForm, GastoForm, ProfileForm
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE IA
# ═══════════════════════════════════════════════════════════════════════════════

model_id = "runwayml/stable-diffusion-v1-5"

try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32

    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch_dtype)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)

except Exception as e:
    print(f"Error cargando modelo IA: {e}")
    pipe = None

# ═══════════════════════════════════════════════════════════════════════════════
# CLASIFICADOR DE GASTOS
# ═══════════════════════════════════════════════════════════════════════════════

KEYWORDS_FIJO = ['renta', 'hipoteca', 'luz', 'agua', 'gas', 'internet', 'teléfono', 'celular', 'seguros', 'nómina', 'colegiatura', 'netflix', 'spotify', 'gym']
KEYWORDS_HORMIGA = ['café', 'oxxo', 'tienda', 'dulces', 'refresco', 'botana', 'snack', 'uber', 'rappi', 'papas', 'chicles']
KEYWORDS_VARIABLE = ['cine', 'restaurante', 'bar', 'fiesta', 'viaje', 'ropa', 'zapatos', 'gadget', 'regalo', 'vacaciones']

def clasificar_gasto_ia(descripcion, monto):
    desc_lower = descripcion.lower().strip()
    monto_float = float(monto)

    score_fijo = 0
    score_hormiga = 0
    score_variable = 0

    for kw in KEYWORDS_FIJO:
        if kw in desc_lower:
            score_fijo += 40
            break

    for kw in KEYWORDS_HORMIGA:
        if kw in desc_lower:
            score_hormiga += 40
            break

    for kw in KEYWORDS_VARIABLE:
        if kw in desc_lower:
            score_variable += 40
            break

    if monto_float <= 100:
        score_hormiga += 25
    elif monto_float <= 500:
        score_variable += 15
        score_hormiga += 10
    else:
        score_fijo += 20

    scores = {'Hormiga': score_hormiga, 'Fijo': score_fijo, 'Variable': score_variable}
    categoria_nombre = max(scores, key=scores.get)

    categoria = CategoriaGasto.query.filter_by(nombre=categoria_nombre).first()
    return categoria, scores

# ═══════════════════════════════════════════════════════════════════════════════
# AVATARES
# ═══════════════════════════════════════════════════════════════════════════════

AVATAR_CATEGORIAS = {
    "profesional": {"nombre": "Profesional", "desc": "a business professional person in formal attire", "emoji": "💼"},
    "astronauta": {"nombre": "Astronauta", "desc": "an astronaut exploring space", "emoji": "🚀"},
    "artista": {"nombre": "Artista", "desc": "a creative artist with paint brushes", "emoji": "🎨"},
    "gamer": {"nombre": "Gamer", "desc": "a gamer with headphones and controller", "emoji": "🎮"},
    "programador": {"nombre": "Programador", "desc": "a software developer with laptop", "emoji": "💻"},
    "robot": {"nombre": "Robot", "desc": "a friendly robot companion", "emoji": "🤖"},
    "gato": {"nombre": "Gato", "desc": "a cute cat with big eyes", "emoji": "🐱"},
}

PROMPT_TEMPLATE = (
    "minimalist avatar icon of {descripcion}, in a consistent Widata platform style, "
    "centered, soft lighting, smooth shading, clean gradient background, modern flat illustration, "
    "friendly, simple and professional, rounded shapes, high quality, 512x512, no text, no watermark"
)

def generar_avatar_prompt(descripcion):
    return PROMPT_TEMPLATE.format(descripcion=descripcion)


def _get_avatar_info(avatar_url, user_id=None):
    """
    Devuelve información del avatar. Ahora soporta iconos estáticos sin usar IA.
    """
    if not avatar_url:
        return {'url': None, 'label': 'Sin avatar', 'type': 'none', 'emoji': '👤'}

    # 1. Avatar personalizado ya generado por IA
    if avatar_url.startswith('/static/avatars/'):
        return {'url': avatar_url, 'label': 'Avatar IA', 'type': 'custom', 'emoji': None}

    # 2. Icono predefinido estático (NUEVA LÓGICA)
    if avatar_url.startswith('icon:'):
        key = avatar_url.replace('icon:', '')
        cat = AVATAR_CATEGORIAS.get(key, {})
        return {
            'url': None, # No hay URL porque es un emoji/icono estático
            'label': cat.get('nombre', key),
            'type': 'predefined',
            'emoji': cat.get('emoji', '👤') # Devuelve el emoji que ya tienes configurado
        }

    return {'url': None, 'label': 'Sin avatar', 'type': 'none', 'emoji': '👤'}


@dashboard.route('/perfil/avatar', methods=['POST'])
@login_required


def seleccionar_avatar():
    try:
        avatar_type = request.form.get('avatar_type', 'predefined')

        # CASO 1: EL USUARIO QUIERE IA (Generación de imagen)
        if avatar_type == 'custom':
            custom_desc = request.form.get('custom_description', '').strip()

            if not custom_desc or len(custom_desc) < 3:
                flash('Escribe una descripción válida para la IA.', 'warning')
                return redirect(url_for('dashboard.perfil'))

            # Aquí SÍ despertamos a la IA
            avatar_url = generar_avatar_ia(custom_desc, current_user.id)
            
            if not avatar_url:
                flash('Error generando avatar IA. Intenta de nuevo.', 'danger')
                return redirect(url_for('dashboard.perfil'))

            current_user.avatar_url = avatar_url
            db.session.commit()
            flash('Avatar IA generado y guardado con éxito.', 'success')

        # CASO 2: EL USUARIO ELIGE UN ICONO (Sin IA)
        else:
            avatar_id = request.form.get('avatar_id', '').strip()

            if avatar_id not in AVATAR_CATEGORIAS:
                flash('Icono inválido.', 'danger')
                return redirect(url_for('dashboard.perfil'))

            # ¡AQUÍ ESTÁ LA MAGIA! 
            # Ya NO llamamos a generar_avatar_ia().
            # Simplemente guardamos un texto que dice "icon:gato" o "icon:gamer"
            current_user.avatar_url = f"icon:{avatar_id}"
            db.session.commit()
            flash('Icono guardado al instante.', 'success')

        return redirect(url_for('dashboard.perfil'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al seleccionar avatar: {str(e)}', 'danger')
        return redirect(url_for('dashboard.perfil'))


def generar_avatar_ia(descripcion, user_id):
    if not pipe:
        print(" El modelo IA no está cargado")
        return None
    prompt = generar_avatar_prompt(descripcion)
    print(f"🔹 Prompt generado: {prompt}")

    try:
        result = pipe(prompt, height=512, width=512, guidance_scale=7.5)
        image = result.images[0]

        ruta = os.path.join("app/static/avatars", f"{user_id}.png")
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        image.save(ruta)
        print(f" Avatar guardado en: {ruta}")

        return f"/static/avatars/{user_id}.png"

    except Exception as e:
        print(f" Error generando avatar: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@dashboard.route('/')
@login_required
def index():
    try:
        creditos = Credito.query.filter_by(usuario_id=current_user.id).order_by(Credito.tasa_anual.desc()).all()
        gastos = Gasto.query.filter_by(usuario_id=current_user.id).order_by(Gasto.fecha.desc()).limit(10).all()

        cat_hormiga = CategoriaGasto.query.filter_by(nombre='Hormiga').first()
        fuga_hormiga = sum(g.monto for g in gastos if cat_hormiga and g.categoria_id == cat_hormiga.id)

        total_deuda = sum(float(c.deuda_actual) for c in creditos)
        total_limite = sum(float(c.limite_credito) for c in creditos)
        total_gastos = sum(float(g.monto) for g in gastos)

        utilizacion = (total_deuda / total_limite * 100) if total_limite > 0 else 0

        return render_template('dashboard/index.html',
            creditos=creditos,
            gastos=gastos,
            fuga_hormiga=fuga_hormiga,
            total_deuda=total_deuda,
            total_limite=total_limite,
            total_gastos=total_gastos,
            utilizacion=utilizacion
        )

    except Exception as e:
        flash(f'❌ Error al cargar dashboard: {str(e)}', 'danger')
        return render_template('dashboard/index.html')

# ═══════════════════════════════════════════════════════════════════════════════
# PERFIL
# ═══════════════════════════════════════════════════════════════════════════════

@dashboard.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        try:
            current_user.nombre = form.nombre.data.strip()
            current_user.apellidos = form.apellidos.data.strip()
            current_user.edad = form.edad.data
            current_user.telefono = form.telefono.data.strip() if form.telefono.data else None

            db.session.commit()
            flash('✅ Perfil actualizado', 'success')
            return redirect(url_for('dashboard.perfil'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'danger')

    avatar_info = _get_avatar_info(current_user.avatar_url)

    return render_template('dashboard/perfil.html',
        form=form,
        avatar_categorias=AVATAR_CATEGORIAS,
        avatar_info=avatar_info
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SCORE (YA FUNCIONA)
# ═══════════════════════════════════════════════════════════════════════════════

@dashboard.route('/score')
@login_required
def score():
    return render_template('dashboard/score.html')

# ═══════════════════════════════════════════════════════════════════════════════
# CALCULADORA
# ═══════════════════════════════════════════════════════════════════════════════

@dashboard.route('/calculadora')
@login_required
def calculadora():
    return render_template('dashboard/calculadora.html')

@dashboard.route('/estrategia', methods=['GET', 'POST'])
@login_required
def estrategia():
    form = CreditoForm()

    try:
        instituciones = Institucion.query.all()
        form.institucion_id.choices = [(i.id, i.nombre) for i in instituciones]

        if form.validate_on_submit():
            credito = Credito(
                usuario_id=current_user.id,
                institucion_id=form.institucion_id.data,
                limite_credito=form.limite_credito.data,
                deuda_actual=form.deuda_actual.data,
                tasa_anual=form.tasa_anual.data,
                pago_minimo=form.pago_minimo.data
            )
            db.session.add(credito)
            db.session.commit()

            flash('✅ Crédito registrado exitosamente', 'success')
            return redirect(url_for('dashboard.estrategia'))

        creditos = Credito.query.filter_by(usuario_id=current_user.id)\
            .order_by(Credito.tasa_anual.desc()).all()

        sort_method = request.args.get('method', 'avalanche')

        if sort_method == 'snowball':
            creditos = sorted(creditos, key=lambda x: x.deuda_actual)
            method_name = "Bola de Nieve"
        else:
            method_name = "Avalancha Matemática"

        return render_template(
            'dashboard/estrategia.html',
            form=form,
            creditos=creditos,
            method_name=method_name
        )

    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error en estrategia: {str(e)}', 'danger')

        return render_template(
            'dashboard/estrategia.html',
            form=form,
            creditos=[],
            method_name="Avalancha Matemática"
        )


@dashboard.route('/fugas', methods=['GET', 'POST'])
@login_required
def fugas():
    form = GastoForm()

    if form.validate_on_submit():
        try:
            categoria, scores = clasificar_gasto_ia(
                form.descripcion.data,
                form.monto.data
            )

            if not categoria:
                flash('❌ No hay categorías en la BD', 'danger')
                return redirect(url_for('dashboard.fugas'))

            gasto = Gasto(
                usuario_id=current_user.id,
                categoria_id=categoria.id,
                descripcion=form.descripcion.data.strip(),
                monto=form.monto.data,
                fecha=form.fecha.data
            )

            db.session.add(gasto)
            db.session.commit()

            flash('✅ Gasto registrado con IA', 'success')
            return redirect(url_for('dashboard.fugas'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'danger')

    try:
        categorias = CategoriaGasto.query.all()
        categorias_dict = {c.id: c.nombre for c in categorias}

        gastos = Gasto.query.filter_by(usuario_id=current_user.id)\
            .order_by(Gasto.fecha.desc()).all()

        cat_hormiga_id = next(
            (c.id for c in categorias if c.nombre == 'Hormiga'),
            None
        )

        fuga_hormiga = sum(
            g.monto for g in gastos if g.categoria_id == cat_hormiga_id
        )

        return render_template(
            'dashboard/fugas.html',
            form=form,
            gastos=gastos,
            fuga_hormiga=fuga_hormiga,
            categorias=categorias_dict
        )

    except Exception as e:
        flash(f'❌ Error cargando fugas: {str(e)}', 'danger')

        return render_template(
            'dashboard/fugas.html',
            form=form,
            gastos=[],
            fuga_hormiga=0,
            categorias={}
        )
    
