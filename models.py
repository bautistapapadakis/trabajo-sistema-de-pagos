"""Modelos de datos del Simulador de Pago/Cobro (B2B y B2C).

Define las entidades principales usando SQLAlchemy:

* ``Usuario``  : personas que usan el sistema (administrador o cliente).
* ``Producto`` : artículos que la empresa pone a la venta.
* ``Pedido``   : orden de compra de un cliente (canal B2C o B2B).
* ``Pago``     : registro del pago/cobro asociado a un pedido.

Relaciones:
    Un usuario tiene muchos pedidos.
    Un producto tiene muchos pedidos.
    Un pedido tiene un único pago (relación 1 a 1).
"""

from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

# Instancia única de SQLAlchemy que se inicializa en app.py con init_app()
db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    """Usuario del sistema.

    El atributo ``rol`` define los permisos:
        * ``"admin"``   : vendedor/empresa, administra productos y cobros.
        * ``"cliente"`` : comprador (consumidor final o empresa).
    """

    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default="cliente", nullable=False)

    # Un usuario puede tener muchos pedidos.
    pedidos = db.relationship("Pedido", backref="usuario", lazy=True)

    def __repr__(self):
        """Representación legible del usuario para depuración."""
        return f"<Usuario {self.email} ({self.rol})>"


class Producto(db.Model):
    """Producto ofrecido por la empresa."""

    __tablename__ = "producto"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(300))
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    # Un producto puede aparecer en muchos pedidos.
    pedidos = db.relationship("Pedido", backref="producto", lazy=True)

    def __repr__(self):
        """Representación legible del producto para depuración."""
        return f"<Producto {self.nombre}>"


class Pedido(db.Model):
    """Pedido de compra.

    Cada pedido corresponde a un producto y una cantidad. La columna
    ``tipo`` distingue el canal de venta:

        * ``"B2C"`` : venta minorista al consumidor final (precio de lista).
        * ``"B2B"`` : venta mayorista a otra empresa (con descuento).
    """

    __tablename__ = "pedido"

    ESTADOS = (
        "Pendiente de pago",
        "Pagado",
        "Cobrado",
        "Cancelado",
    )

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    cantidad = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), default="Pendiente de pago")
    tipo = db.Column(db.String(10), default="B2C", nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)

    # Relación 1 a 1: un pedido tiene un pago.
    pago = db.relationship("Pago", backref="pedido", uselist=False)

    def __repr__(self):
        """Representación legible del pedido para depuración."""
        return f"<Pedido {self.id} {self.tipo} {self.estado}>"


class Pago(db.Model):
    """Pago (o cobro) asociado a un pedido.

    Se crea cuando el cliente completa el simulador de pago. El campo
    ``metodo`` guarda el medio elegido (tarjeta, transferencia, etc.).
    """

    __tablename__ = "pago"

    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(50), default="Aprobado")
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)

    def __repr__(self):
        """Representación legible del pago para depuración."""
        return f"<Pago {self.id} ${self.monto} {self.estado}>"
