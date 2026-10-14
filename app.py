"""Simulador de Pago/Cobro (B2B y B2C).

Aplicación web desarrollada con Flask que simula el ciclo completo de
una compra:

1. El administrador (empresa) gestiona el catálogo de productos.
2. El cliente (consumidor o empresa) crea pedidos por canal B2C o B2B.
3. El cliente paga el pedido mediante un simulador de pago.
4. El administrador registra el cobro y actualiza el estado del pedido.

Módulos del proyecto:
    * ``models.py`` : modelos de datos (Usuario, Producto, Pedido, Pago).
    * ``forms.py``  : formularios Flask-WTF con validaciones.
    * ``templates/``: vistas HTML renderizadas con Jinja2.
    * ``static/``   : hoja de estilos.

Para ejecutar: ``python app.py`` y abrir http://127.0.0.1:5000
"""

from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from forms import (
    LoginForm,
    PagoForm,
    PedidoForm,
    ProductoForm,
    RegistroForm,
)
from models import Pago, Pedido, Producto, Usuario, db

# ---------------------------------------------------------------------------
# Constantes de negocio (canal B2B)
# ---------------------------------------------------------------------------

# Descuento aplicado a los pedidos mayoristas (B2B).
DESCUENTO_B2B = 0.10
# Cantidad mínima para poder generar un pedido B2B.
CANTIDAD_MINIMA_B2B = 10

# ---------------------------------------------------------------------------
# Configuración de la aplicación
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = "clave-secreta-cambiar-en-produccion"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///simulador.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Protección CSRF para todos los formularios POST (incluye los que no son
# FlaskForm, como los botones de eliminar/cobrar).
csrf = CSRFProtect()
csrf.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Iniciá sesión para continuar."


@login_manager.user_loader
def cargar_usuario(user_id):
    """Recupera un usuario a partir de su id (lo usa Flask-Login)."""
    return db.session.get(Usuario, int(user_id))


# ---------------------------------------------------------------------------
# Decoradores de control de acceso
# ---------------------------------------------------------------------------


def rol_requerido(rol):
    """Devuelve un decorador que exige un rol determinado.

    Uso: ``@rol_requerido("admin")``. Si el usuario no tiene el rol
    indicado responde con un error 403.
    """

    def decorador(funcion):
        @wraps(funcion)
        @login_required
        def envoltura(*args, **kwargs):
            if current_user.rol != rol:
                abort(403)
            return funcion(*args, **kwargs)

        return envoltura

    return decorador


# ---------------------------------------------------------------------------
# Página principal y autenticación
# ---------------------------------------------------------------------------


@app.route("/")
def inicio():
    """Página de bienvenida. Redirige al panel según el rol."""
    if current_user.is_authenticated:
        if current_user.rol == "admin":
            return redirect(url_for("admin"))
        return redirect(url_for("cliente"))

    return render_template("inicio.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    """Registra un nuevo cliente."""
    form = RegistroForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if Usuario.query.filter_by(email=email).first():
            flash("Ese email ya está registrado. Probá con otro.", "error")
            return render_template("registro.html", form=form)

        usuario = Usuario(
            nombre=form.nombre.data.strip(),
            email=email,
            password=generate_password_hash(form.password.data),
            rol="cliente",
        )
        db.session.add(usuario)
        db.session.commit()

        flash("Cuenta creada. Ya podés iniciar sesión.", "exito")
        return redirect(url_for("login"))

    return render_template("registro.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicia sesión de un usuario existente."""
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, form.password.data):
            login_user(usuario)
            return redirect(url_for("inicio"))

        flash("Email o contraseña incorrectos.", "error")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    """Cierra la sesión del usuario actual."""
    logout_user()
    flash("Sesión cerrada.", "exito")
    return redirect(url_for("inicio"))


# ---------------------------------------------------------------------------
# Paneles
# ---------------------------------------------------------------------------


@app.route("/cliente")
@rol_requerido("cliente")
def cliente():
    """Panel principal del cliente."""
    pedidos = (
        Pedido.query.filter_by(usuario_id=current_user.id)
        .order_by(Pedido.id.desc())
        .all()
    )
    return render_template("cliente.html", pedidos=pedidos)


@app.route("/admin")
@rol_requerido("admin")
def admin():
    """Panel principal del administrador (empresa)."""
    total_productos = Producto.query.count()
    total_pedidos = Pedido.query.count()
    por_cobrar = Pedido.query.filter_by(estado="Pagado").count()
    return render_template(
        "admin.html",
        total_productos=total_productos,
        total_pedidos=total_pedidos,
        por_cobrar=por_cobrar,
    )


# ---------------------------------------------------------------------------
# Gestión de productos (solo administrador)
# ---------------------------------------------------------------------------


@app.route("/productos")
@rol_requerido("admin")
def productos():
    """Lista todos los productos registrados."""
    lista_productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("productos.html", productos=lista_productos)


@app.route("/productos/nuevo", methods=["GET", "POST"])
@rol_requerido("admin")
def nuevo_producto():
    """Crea un nuevo producto."""
    form = ProductoForm()

    if form.validate_on_submit():
        producto = Producto(
            nombre=form.nombre.data.strip(),
            descripcion=form.descripcion.data,
            precio=form.precio.data,
            stock=form.stock.data,
        )
        db.session.add(producto)
        db.session.commit()
        flash("Producto agregado correctamente.", "exito")
        return redirect(url_for("productos"))

    return render_template("nuevo_producto.html", form=form)


@app.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
@rol_requerido("admin")
def editar_producto(producto_id):
    """Edita un producto existente."""
    producto = db.get_or_404(Producto, producto_id)
    form = ProductoForm(obj=producto)

    if form.validate_on_submit():
        producto.nombre = form.nombre.data.strip()
        producto.descripcion = form.descripcion.data
        producto.precio = form.precio.data
        producto.stock = form.stock.data
        db.session.commit()
        flash("Producto actualizado correctamente.", "exito")
        return redirect(url_for("productos"))

    return render_template(
        "editar_producto.html", form=form, producto=producto
    )


@app.route("/productos/<int:producto_id>/eliminar", methods=["POST"])
@rol_requerido("admin")
def eliminar_producto(producto_id):
    """Elimina un producto. No permite borrar productos con pedidos."""
    producto = db.get_or_404(Producto, producto_id)

    if producto.pedidos:
        flash(
            "No se puede eliminar: el producto tiene pedidos asociados.",
            "error",
        )
        return redirect(url_for("productos"))

    db.session.delete(producto)
    db.session.commit()
    flash("Producto eliminado.", "exito")
    return redirect(url_for("productos"))


# ---------------------------------------------------------------------------
# Catálogo y pedidos (cliente)
# ---------------------------------------------------------------------------


@app.route("/catalogo")
@rol_requerido("cliente")
def catalogo():
    """Muestra los productos con stock disponible."""
    lista_productos = (
        Producto.query.filter(Producto.stock > 0)
        .order_by(Producto.nombre)
        .all()
    )
    return render_template("catalogo.html", productos=lista_productos)


@app.route("/pedidos")
@rol_requerido("cliente")
def mis_pedidos():
    """Lista los pedidos del cliente actual."""
    pedidos = (
        Pedido.query.filter_by(usuario_id=current_user.id)
        .order_by(Pedido.id.desc())
        .all()
    )
    return render_template("mis_pedidos.html", pedidos=pedidos)


@app.route("/pedidos/nuevo", methods=["GET", "POST"])
@rol_requerido("cliente")
def nuevo_pedido():
    """Crea un pedido nuevo.

    - En canal B2C se cobra el precio de lista.
    - En canal B2B se exige una cantidad mínima y se aplica descuento.
    """
    form = PedidoForm()

    # Cargar los productos disponibles en el selector.
    productos_disponibles = Producto.query.filter(Producto.stock > 0).all()
    form.producto.choices = [
        (p.id, f"{p.nombre} - ${p.precio:.2f} (stock {p.stock})")
        for p in productos_disponibles
    ]

    if not productos_disponibles:
        flash("No hay productos disponibles para pedir.", "error")
        return redirect(url_for("catalogo"))

    if form.validate_on_submit():
        producto = db.session.get(Producto, form.producto.data)
        cantidad = form.cantidad.data
        tipo = form.tipo.data

        if producto is None:
            flash("Producto inválido.", "error")
            return redirect(url_for("nuevo_pedido"))

        if producto.stock < cantidad:
            flash(
                f"Stock insuficiente. Disponible: {producto.stock}.",
                "error",
            )
            return render_template("nuevo_pedido.html", form=form)

        if tipo == "B2B" and cantidad < CANTIDAD_MINIMA_B2B:
            flash(
                f"Los pedidos B2B requieren al menos "
                f"{CANTIDAD_MINIMA_B2B} unidades.",
                "error",
            )
            return render_template("nuevo_pedido.html", form=form)

        # Cálculo del total según el canal de venta.
        subtotal = producto.precio * cantidad
        total = subtotal * (1 - DESCUENTO_B2B) if tipo == "B2B" else subtotal

        pedido = Pedido(
            cantidad=cantidad,
            total=round(total, 2),
            tipo=tipo,
            estado="Pendiente de pago",
            usuario_id=current_user.id,
            producto_id=producto.id,
        )

        # Reservar stock al crear el pedido.
        producto.stock -= cantidad

        db.session.add(pedido)
        db.session.commit()

        flash("Pedido creado. Ahora podés pagarlo.", "exito")
        return redirect(url_for("mis_pedidos"))

    return render_template("nuevo_pedido.html", form=form)


@app.route("/pedidos/<int:pedido_id>/pagar", methods=["GET", "POST"])
@rol_requerido("cliente")
def pagar_pedido(pedido_id):
    """Simulador de pago: registra el pago y actualiza el pedido."""
    pedido = db.get_or_404(Pedido, pedido_id)

    if pedido.usuario_id != current_user.id:
        abort(403)

    if pedido.estado != "Pendiente de pago":
        flash("Este pedido ya no admite pagos.", "error")
        return redirect(url_for("mis_pedidos"))

    form = PagoForm()

    if form.validate_on_submit():
        # En un entorno real aquí se contactaría a la pasarela de pago.
        pago = Pago(
            monto=pedido.total,
            metodo=form.metodo.data,
            estado="Aprobado",
            fecha=datetime.utcnow(),
            pedido_id=pedido.id,
        )
        pedido.estado = "Pagado"

        db.session.add(pago)
        db.session.commit()

        flash(
            f"Pago aprobado por ${pedido.total:.2f}. Pedido pagado.",
            "exito",
        )
        return redirect(url_for("mis_pedidos"))

    return render_template("pago.html", form=form, pedido=pedido)


@app.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@rol_requerido("cliente")
def cancelar_pedido(pedido_id):
    """Cancela un pedido pendiente y devuelve el stock reservado."""
    pedido = db.get_or_404(Pedido, pedido_id)

    if pedido.usuario_id != current_user.id:
        abort(403)

    if pedido.estado != "Pendiente de pago":
        flash("Solo se pueden cancelar pedidos pendientes de pago.", "error")
        return redirect(url_for("mis_pedidos"))

    # Devolver stock.
    pedido.producto.stock += pedido.cantidad
    pedido.estado = "Cancelado"
    db.session.commit()

    flash("Pedido cancelado.", "exito")
    return redirect(url_for("mis_pedidos"))


# ---------------------------------------------------------------------------
# Gestión de pedidos y cobros (administrador)
# ---------------------------------------------------------------------------


@app.route("/admin/pedidos")
@rol_requerido("admin")
def admin_pedidos():
    """Lista todos los pedidos para su gestión y cobro."""
    pedidos = Pedido.query.order_by(Pedido.id.desc()).all()
    return render_template("admin_pedidos.html", pedidos=pedidos)


@app.route("/admin/pedidos/<int:pedido_id>/cobrar", methods=["POST"])
@rol_requerido("admin")
def cobrar_pedido(pedido_id):
    """Registra el cobro de un pedido que ya fue pagado por el cliente."""
    pedido = db.get_or_404(Pedido, pedido_id)

    if pedido.estado != "Pagado":
        flash("Solo se pueden cobrar pedidos en estado 'Pagado'.", "error")
        return redirect(url_for("admin_pedidos"))

    pedido.estado = "Cobrado"
    db.session.commit()
    flash(f"Cobro registrado para el pedido #{pedido.id}.", "exito")
    return redirect(url_for("admin_pedidos"))


# ---------------------------------------------------------------------------
# Manejo de errores
# ---------------------------------------------------------------------------


@app.errorhandler(403)
def acceso_denegado(error):
    """Muestra una página amigable cuando falta permiso."""
    return render_template("error.html", codigo=403,
                           mensaje="Acceso denegado."), 403


@app.errorhandler(404)
def no_encontrado(error):
    """Muestra una página amigable cuando el recurso no existe."""
    return render_template("error.html", codigo=404,
                           mensaje="Recurso no encontrado."), 404


# ---------------------------------------------------------------------------
# Inicialización de la base de datos
# ---------------------------------------------------------------------------


def asegurar_columnas():
    """Agrega columnas nuevas a bases de datos creadas con versiones previas.

    SQLite no incorpora columnas automáticamente mediante ``create_all`` cuando
    la tabla ya existe, por eso se verifica y se hace ``ALTER TABLE``.
    """
    with db.engine.begin() as conexion:
        columnas = conexion.exec_driver_sql(
            "PRAGMA table_info(usuario)"
        ).fetchall()
        nombres = [col[1] for col in columnas]
        if "rol" not in nombres:
            conexion.exec_driver_sql(
                "ALTER TABLE usuario ADD COLUMN rol VARCHAR(20) "
                "NOT NULL DEFAULT 'cliente'"
            )

        columnas = conexion.exec_driver_sql(
            "PRAGMA table_info(pedido)"
        ).fetchall()
        nombres = [col[1] for col in columnas]
        if nombres and "tipo" not in nombres:
            conexion.exec_driver_sql(
                "ALTER TABLE pedido ADD COLUMN tipo VARCHAR(10) "
                "NOT NULL DEFAULT 'B2C'"
            )


def crear_administrador():
    """Crea (o actualiza) la cuenta de administrador por defecto."""
    email = "admin@simulador.com"
    password = "admin123"

    administrador = Usuario.query.filter_by(email=email).first()

    if administrador is None:
        administrador = Usuario(
            nombre="Administrador",
            email=email,
            password=generate_password_hash(password),
            rol="admin",
        )
        db.session.add(administrador)
    else:
        administrador.rol = "admin"
        administrador.password = generate_password_hash(password)

    db.session.commit()


def crear_productos_de_ejemplo():
    """Carga productos de ejemplo la primera vez que arranca la app."""
    if Producto.query.count() > 0:
        return

    ejemplos = [
        ("Teclado mecánico", "Teclado RGB switches rojos", 45000.0, 50),
        ("Mouse inalámbrico", "Mouse ergonómico 1600 dpi", 22000.0, 80),
        ("Monitor 24''", "Monitor Full HD IPS 75 Hz", 180000.0, 20),
        ("Auriculares", "Auriculares con micrófono", 32000.0, 40),
        ("Webcam HD", "Cámara web 1080p para streaming", 55000.0, 15),
    ]

    for nombre, descripcion, precio, stock in ejemplos:
        db.session.add(
            Producto(
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                stock=stock,
            )
        )

    db.session.commit()


def inicializar_base_de_datos():
    """Crea las tablas y carga los datos iniciales."""
    db.create_all()
    asegurar_columnas()
    crear_administrador()
    crear_productos_de_ejemplo()


with app.app_context():
    inicializar_base_de_datos()


if __name__ == "__main__":
    app.run(debug=True)
