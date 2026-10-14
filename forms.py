"""Formularios del Simulador de Pago/Cobro usando Flask-WTF.

Cada clase representa un formulario HTML con sus validaciones:

* ``RegistroForm``  : alta de nuevos clientes.
* ``LoginForm``     : inicio de sesión.
* ``ProductoForm``  : alta y edición de productos.
* ``PedidoForm``    : creación de pedidos (canal B2C o B2B).
* ``PagoForm``      : simulador de pago/cobro.

Todos los formularios incluyen protección CSRF de forma automática.
"""

from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange

# Medios de pago disponibles en el simulador.
METODOS_PAGO = [
    ("Tarjeta de crédito", "Tarjeta de crédito"),
    ("Tarjeta de débito", "Tarjeta de débito"),
    ("Transferencia bancaria", "Transferencia bancaria"),
    ("Mercado Pago", "Mercado Pago"),
    ("Efectivo", "Efectivo"),
]

# Canales de venta soportados.
TIPOS_VENTA = [
    ("B2C", "B2C - Minorista (consumidor final)"),
    ("B2B", "B2B - Mayorista (empresa)"),
]


class RegistroForm(FlaskForm):
    """Formulario de registro de nuevos clientes."""

    nombre = StringField(
        "Nombre",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    password = PasswordField(
        "Contraseña",
        validators=[DataRequired(), Length(min=6)],
    )
    submit = SubmitField("Registrarse")


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    password = PasswordField(
        "Contraseña",
        validators=[DataRequired()],
    )
    submit = SubmitField("Iniciar sesión")


class ProductoForm(FlaskForm):
    """Formulario para agregar o editar un producto."""

    nombre = StringField(
        "Nombre del producto",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    descripcion = TextAreaField("Descripción")
    precio = FloatField(
        "Precio",
        validators=[DataRequired(), NumberRange(min=0.01)],
    )
    stock = IntegerField(
        "Cantidad en stock",
        validators=[DataRequired(), NumberRange(min=0)],
    )
    submit = SubmitField("Guardar producto")


class PedidoForm(FlaskForm):
    """Formulario para que el cliente cree un pedido.

    El campo ``producto`` se llena dinámicamente con los productos
    disponibles desde la vista correspondiente.
    """

    producto = SelectField(
        "Producto",
        coerce=int,
        validators=[DataRequired()],
    )
    cantidad = IntegerField(
        "Cantidad",
        validators=[DataRequired(), NumberRange(min=1)],
    )
    tipo = SelectField(
        "Tipo de venta",
        choices=TIPOS_VENTA,
        validators=[DataRequired()],
    )
    submit = SubmitField("Crear pedido")


class PagoForm(FlaskForm):
    """Formulario del simulador de pago/cobro.

    Los datos de tarjeta son simulados: se validan de forma básica para
    dar realismo pero no se envían a ningún servicio externo.
    """

    metodo = SelectField(
        "Medio de pago",
        choices=METODOS_PAGO,
        validators=[DataRequired()],
    )
    titular = StringField(
        "Titular de la tarjeta",
        validators=[Length(max=100)],
    )
    numero_tarjeta = StringField(
        "Número de tarjeta (simulado)",
        validators=[Length(max=30)],
    )
    vencimiento = StringField(
        "Vencimiento (MM/AA)",
        validators=[Length(max=10)],
    )
    cvv = StringField(
        "CVV",
        validators=[Length(max=4)],
    )
    submit = SubmitField("Confirmar pago")
