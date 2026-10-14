# Simulador de Pago/Cobro (B2B y B2C)

Aplicación web desarrollada con **Python y Flask** que simula el ciclo
completo de una venta: gestión de productos, creación de pedidos, pago del
cliente y registro de cobros por parte de la empresa.

Forma parte del **TP 4 – B2B y B2C – Integración**.

## Funcionalidades

- **Registro y autenticación de usuarios** con `Flask-Login`
  (registro, inicio y cierre de sesión) y contraseñas hasheadas.
- **Roles**: `admin` (empresa/vendedor) y `cliente` (comprador).
- **Gestión de productos** (solo admin): listar, agregar, editar y eliminar.
- **Sistema de pedidos** (cliente): crear y gestionar pedidos.
- **Canales de venta**:
  - **B2C** (minorista): venta al consumidor final a precio de lista.
  - **B2B** (mayorista): venta a empresas con cantidad mínima de 10 unidades
    y **10% de descuento**.
- **Simulador de pago/cobro**: interfaz para simular el pago del pedido y,
  desde el panel del administrador, registrar el cobro. Al pagar, el estado
  del pedido se actualiza automáticamente.
- **Control de stock**: se reserva al crear el pedido y se devuelve al
  cancelarlo.

### Estados de un pedido

```
Pendiente de pago  ->  Pagado  ->  Cobrado
        |
        +----------->  Cancelado
```

## Tecnologías utilizadas

| Tecnología       | Uso                                        |
| ---------------- | ------------------------------------------ |
| Python 3         | Lenguaje base                              |
| Flask            | Framework web                              |
| Flask-Login      | Autenticación y sesiones                   |
| Flask-WTF / WTForms | Formularios y validaciones + CSRF       |
| Flask-SQLAlchemy | ORM y modelos de datos                     |
| SQLite           | Base de datos (archivo `instance/simulador.db`) |
| Jinja2           | Plantillas HTML                            |
| HTML5 + CSS3     | Interfaz de usuario                        |

## Estructura del proyecto

```
simulador_pago/
├── app.py            # Rutas, lógica de negocio y arranque de la app
├── models.py         # Modelos: Usuario, Producto, Pedido, Pago
├── forms.py          # Formularios Flask-WTF
├── requirements.txt  # Dependencias
├── instance/
│   └── simulador.db  # Base de datos SQLite (se crea sola)
├── static/
│   └── style.css     # Hoja de estilos
└── templates/        # Vistas HTML (Jinja2)
    ├── base.html
    ├── inicio.html
    ├── registro.html
    ├── login.html
    ├── cliente.html
    ├── admin.html
    ├── productos.html
    ├── nuevo_producto.html
    ├── editar_producto.html
    ├── catalogo.html
    ├── nuevo_pedido.html
    ├── mis_pedidos.html
    ├── pago.html
    ├── admin_pedidos.html
    └── error.html
```

## Instalación y ejecución

1. Clonar o descargar el proyecto y entrar a la carpeta:

   ```bash
   cd simulador_pago
   ```

2. Crear y activar un entorno virtual (opcional pero recomendado):

   ```powershell
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Ejecutar la aplicación:

   ```bash
   python app.py
   ```

5. Abrir en el navegador: <http://127.0.0.1:5000>

La base de datos y los datos de ejemplo se crean automáticamente la primera
vez que se ejecuta la aplicación.

## Cuentas de prueba

| Rol           | Email                 | Contraseña |
| ------------- | --------------------- | ---------- |
| Administrador | `admin@simulador.com` | `admin123` |

Los clientes se pueden crear desde la opción **Registrarse** de la página de
inicio.

## Flujo de uso (demostración)

1. Ingresar como **administrador** y revisar/agregar productos.
2. Registrar un **cliente** e iniciar sesión con esa cuenta.
3. Desde **Catálogo / Crear pedido**, generar un pedido indicando producto,
   cantidad y tipo de venta (B2C o B2B).
4. En **Mis pedidos**, presionar **Pagar** y completar el simulador de pago.
5. Volver a la cuenta de **administrador**, entrar a **Pedidos** y presionar
   **Registrar cobro** para cerrar el ciclo.

## Modelo de datos

- **Usuario**: `id`, `nombre`, `email`, `password`, `rol`.
  *Un usuario tiene muchos pedidos.*
- **Producto**: `id`, `nombre`, `descripcion`, `precio`, `stock`.
  *Un producto aparece en muchos pedidos.*
- **Pedido**: `id`, `fecha`, `cantidad`, `total`, `estado`, `tipo`,
  `usuario_id`, `producto_id`.
- **Pago**: `id`, `monto`, `metodo`, `estado`, `fecha`, `pedido_id`.
  *Un pedido tiene un pago (relación 1 a 1).*

## Notas

- El módulo de pago es **simulado**: no se conecta a ninguna pasarela real ni
  se envían datos a servicios externos.
- Para reiniciar los datos, eliminar el archivo `instance/simulador.db` y
  volver a ejecutar la aplicación.
