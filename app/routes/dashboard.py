from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.financial import Credito, Gasto, Institucion, CategoriaGasto
from app.forms import CreditoForm, GastoForm, ProfileForm


dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard.route('/')
@login_required
def index():
    # Obtener créditos para estrategia
    creditos = Credito.query.filter_by(usuario_id=current_user.id).order_by(Credito.tasa_anual.desc()).all()
    
    # Obtener gastos recientes
    gastos = Gasto.query.filter_by(usuario_id=current_user.id).order_by(Gasto.fecha.desc()).limit(10).all()
    
    # Calculo fuga hormiga
    cat_hormiga = CategoriaGasto.query.filter_by(nombre='Hormiga').first()
    fuga_hormiga = sum(g.monto for g in gastos if g.categoria_id == cat_hormiga.id) if cat_hormiga else 0

    # Estadísticas adicionales
    total_deuda = sum(float(c.deuda_actual) for c in creditos)
    total_limite = sum(float(c.limite_credito) for c in creditos)
    total_gastos = sum(float(g.monto) for g in gastos)
    num_creditos = len(creditos)
    num_gastos = len(gastos)

    # Porcentaje de utilización
    utilizacion = (total_deuda / total_limite * 100) if total_limite > 0 else 0

    return render_template('dashboard/index.html',
        creditos=creditos, gastos=gastos, fuga_hormiga=fuga_hormiga,
        total_deuda=total_deuda, total_limite=total_limite,
        total_gastos=total_gastos, num_creditos=num_creditos,
        num_gastos=num_gastos, utilizacion=utilizacion
    )

@dashboard.route('/estrategia', methods=['GET', 'POST'])
@login_required
def estrategia():
    form = CreditoForm()
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
        flash('Crédito registrado exitosamente', 'success')
        return redirect(url_for('dashboard.estrategia'))

    creditos = Credito.query.filter_by(usuario_id=current_user.id).order_by(Credito.tasa_anual.desc()).all()
    
    # Check method (Avalanche or Snowball)
    sort_method = request.args.get('method', 'avalanche')
    if sort_method == 'snowball':
        creditos = sorted(creditos, key=lambda x: x.deuda_actual)
        method_name = "Bola de Nieve"
    else:
        # Default avalanche (highest interest first)
        method_name = "Avalancha Matemática"

    return render_template('dashboard/estrategia.html', form=form, creditos=creditos, method_name=method_name)

@dashboard.route('/fugas', methods=['GET', 'POST'])
@login_required
def fugas():
    form = GastoForm()
    categorias = CategoriaGasto.query.all()
    form.categoria_id.choices = [(c.id, c.nombre) for c in categorias]

    if form.validate_on_submit():
        gasto = Gasto(
            usuario_id=current_user.id,
            categoria_id=form.categoria_id.data,
            descripcion=form.descripcion.data,
            monto=form.monto.data,
            fecha=form.fecha.data
        )
        db.session.add(gasto)
        db.session.commit()
        flash('Gasto registrado exitosamente', 'success')
        return redirect(url_for('dashboard.fugas'))
        
    categorias_dict = {c.id: c.nombre for c in categorias}
    gastos = Gasto.query.filter_by(usuario_id=current_user.id).order_by(Gasto.fecha.desc()).all()
    
    cat_hormiga_id = next((c.id for c in categorias if c.nombre == 'Hormiga'), None)
    fuga_hormiga = sum(g.monto for g in gastos if g.categoria_id == cat_hormiga_id)

    return render_template('dashboard/fugas.html', form=form, gastos=gastos, fuga_hormiga=fuga_hormiga, categorias=categorias_dict)

@dashboard.route('/score')
@login_required
def score():
    # El score real se obtiene via AJAX desde /api/score
    return render_template('dashboard/score.html')


# ═══════════════════════════════════════════════════════════════════════════════
# NUEVAS FUNCIONALIDADES
# ═══════════════════════════════════════════════════════════════════════════════

@dashboard.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.nombre = form.nombre.data
        current_user.apellidos = form.apellidos.data
        current_user.edad = form.edad.data
        current_user.telefono = form.telefono.data
        db.session.commit()
        flash('Perfil actualizado exitosamente', 'success')
        return redirect(url_for('dashboard.perfil'))
    return render_template('dashboard/perfil.html', form=form)


@dashboard.route('/calculadora')
@login_required
def calculadora():
    return render_template('dashboard/calculadora.html')


@dashboard.route('/api/calcular', methods=['POST'])
@login_required
def api_calcular():
    """API interna para la calculadora financiera"""
    data = request.get_json()
    tipo = data.get('tipo', 'deuda')
    
    if tipo == 'deuda':
        deuda = float(data.get('deuda', 0))
        tasa = float(data.get('tasa', 0)) / 100 / 12  # mensual
        pago = float(data.get('pago', 0))
        
        if pago <= 0 or deuda <= 0:
            return jsonify({'error': 'Valores inválidos'}), 400
        
        meses = 0
        total_pagado = 0
        saldo = deuda
        historial = []
        
        while saldo > 0 and meses < 600:  # máx 50 años
            interes = saldo * tasa
            abono = min(pago, saldo + interes)
            saldo = saldo + interes - abono
            total_pagado += abono
            meses += 1
            if meses % 3 == 0 or saldo <= 0:  # cada 3 meses
                historial.append({'mes': meses, 'saldo': round(max(0, saldo), 2)})
        
        return jsonify({
            'meses': meses,
            'anios': round(meses / 12, 1),
            'total_pagado': round(total_pagado, 2),
            'intereses': round(total_pagado - deuda, 2),
            'historial': historial
        })
    
    elif tipo == 'ahorro':
        meta = float(data.get('meta', 0))
        ahorro_mensual = float(data.get('ahorro', 0))
        tasa_rendimiento = float(data.get('rendimiento', 0)) / 100 / 12
        
        if ahorro_mensual <= 0 or meta <= 0:
            return jsonify({'error': 'Valores inválidos'}), 400
        
        meses = 0
        acumulado = 0
        historial = []
        
        while acumulado < meta and meses < 600:
            rendimiento = acumulado * tasa_rendimiento
            acumulado += ahorro_mensual + rendimiento
            meses += 1
            if meses % 3 == 0 or acumulado >= meta:
                historial.append({'mes': meses, 'acumulado': round(min(acumulado, meta), 2)})
        
        return jsonify({
            'meses': meses,
            'anios': round(meses / 12, 1),
            'total_aportado': round(ahorro_mensual * meses, 2),
            'rendimientos': round(acumulado - (ahorro_mensual * meses), 2),
            'historial': historial
        })
    
    return jsonify({'error': 'Tipo no válido'}), 400
