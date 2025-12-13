from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    nit = db.Column(db.String(50), nullable=True)

    # Una clienta puede tener muchas órdenes
    ordenes = db.relationship("Orden", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente {self.nombre}>"


class Tienda(db.Model):
    __tablename__ = "tiendas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), unique=True, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Una tienda puede tener muchos productos
    productos = db.relationship("Producto", back_populates="tienda")

    def __repr__(self):
        return f"<Tienda {self.nombre}>"


class CategoriaProducto(db.Model):
    __tablename__ = "categorias_productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Una categoría puede tener muchos productos
    productos = db.relationship("Producto", back_populates="categoria")

    def __repr__(self):
        return f"<CategoriaProducto {self.nombre}>"


class MarcaProducto(db.Model):
    __tablename__ = "marcas_productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Una marca puede tener muchos productos
    productos = db.relationship("Producto", back_populates="marca")

    def __repr__(self):
        return f"<MarcaProducto {self.nombre}>"


class Talla(db.Model):
    __tablename__ = "tallas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Una talla puede estar asociada a muchos productos
    productos = db.relationship("Producto", back_populates="talla")

    def __repr__(self):
        return f"<Talla {self.nombre}>"


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)

    sku = db.Column(db.String(64), nullable=True, index=True)

    # 🔹 Tienda (FK) – un producto pertenece a una tienda
    tienda_id = db.Column(
        db.Integer,
        db.ForeignKey("tiendas.id"),
        nullable=False
    )
    tienda = db.relationship("Tienda", back_populates="productos")

    # 🔹 Marca (FK)
    marca_id = db.Column(
        db.Integer,
        db.ForeignKey("marcas_productos.id"),
        nullable=True
    )
    marca = db.relationship("MarcaProducto", back_populates="productos")

    descripcion = db.Column(db.String(255), nullable=False)

    # 🔹 Categoría (FK)
    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias_productos.id"),
        nullable=True
    )
    categoria = db.relationship("CategoriaProducto", back_populates="productos")

    # 🔹 Talla (FK opcional)
    talla_id = db.Column(
        db.Integer,
        db.ForeignKey("tallas.id"),
        nullable=True
    )
    talla = db.relationship("Talla", back_populates="productos")

    costo = db.Column(Numeric(10, 2), nullable=False)
    precio = db.Column(Numeric(10, 2), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    imagen = db.Column(db.Text)

    orden_items = db.relationship("OrdenItem", back_populates="producto")

    def __repr__(self):
        return f"<Producto {self.id} - {self.descripcion}>"


class Orden(db.Model):
    __tablename__ = "ordenes"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    descuento = db.Column(Numeric(10, 2), nullable=False, default=0)
    total = db.Column(Numeric(10, 2), nullable=False, default=0)

    # Relación con cliente (muchas órdenes -> un cliente)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    cliente = db.relationship("Cliente", back_populates="ordenes")

    # Items de esta orden (solo productos)
    items = db.relationship(
        "OrdenItem",
        back_populates="orden",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Orden {self.codigo}>"


class OrdenItem(db.Model):
    """
    Representa un renglón dentro de una orden (solo productos).
    """
    __tablename__ = "orden_items"

    id = db.Column(db.Integer, primary_key=True)

    # Relación con la orden
    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes.id"), nullable=False)
    orden = db.relationship("Orden", back_populates="items")

    # FK a producto
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="orden_items")

    # Campos adicionales del item
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)  # snapshot del precio

    def __repr__(self):
        return f"<OrdenItem prod={self.producto_id} x{self.cantidad}>"


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str):
        """Genera y guarda el hash de la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica si la contraseña coincide con el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Usuario {self.username} (admin={self.is_admin})>"


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    memberships = db.relationship("Membership", back_populates="client")
    bookings = db.relationship("Booking", back_populates="client")

    def __repr__(self):
        return f"<Client {self.nombre}>"


class Coach(db.Model):
    __tablename__ = "coaches"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    class_templates = db.relationship("ClassTemplate", back_populates="coach")
    class_sessions = db.relationship("ClassSession", back_populates="coach")

    def __repr__(self):
        return f"<Coach {self.nombre}>"


class MembershipPlan(db.Model):
    __tablename__ = "membership_plans"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    max_clases_por_semana = db.Column(db.Integer, nullable=True)
    max_clases_totales = db.Column(db.Integer, nullable=True)
    duracion_dias = db.Column(db.Integer, nullable=True)
    precio = db.Column(Numeric(10, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    memberships = db.relationship("Membership", back_populates="plan")

    def __repr__(self):
        return f"<MembershipPlan {self.nombre}>"


class Membership(db.Model):
    __tablename__ = "memberships"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("membership_plans.id"), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    clases_usadas = db.Column(db.Integer, default=0, nullable=False)

    client = db.relationship("Client", back_populates="memberships")
    plan = db.relationship("MembershipPlan", back_populates="memberships")
    bookings = db.relationship("Booking", back_populates="membership")

    def __repr__(self):
        return f"<Membership client={self.client_id} plan={self.plan_id}>"


class ClassTemplate(db.Model):
    __tablename__ = "class_templates"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey("coaches.id"), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0-6
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    capacidad = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)

    coach = db.relationship("Coach", back_populates="class_templates")
    class_sessions = db.relationship("ClassSession", back_populates="template")

    def __repr__(self):
        return f"<ClassTemplate {self.nombre} ({self.dia_semana})>"


class ClassSession(db.Model):
    __tablename__ = "class_sessions"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("class_templates.id"), nullable=True)
    fecha = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey("coaches.id"), nullable=False)
    capacidad = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default="Programada")
    nota = db.Column(db.Text, nullable=True)

    template = db.relationship("ClassTemplate", back_populates="class_sessions")
    coach = db.relationship("Coach", back_populates="class_sessions")
    bookings = db.relationship("Booking", back_populates="session")

    def __repr__(self):
        return f"<ClassSession {self.fecha} {self.hora_inicio}-{self.hora_fin}>"


class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (
        db.UniqueConstraint("session_id", "client_id", name="uq_booking_session_client"),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("class_sessions.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    membership_id = db.Column(db.Integer, db.ForeignKey("memberships.id"), nullable=True)
    estado = db.Column(db.String(50), nullable=False)
    asistio = db.Column(db.Boolean, default=False, nullable=False)
    check_in_at = db.Column(db.DateTime, nullable=True)

    session = db.relationship("ClassSession", back_populates="bookings")
    client = db.relationship("Client", back_populates="bookings")
    membership = db.relationship("Membership", back_populates="bookings")

    def __repr__(self):
        return f"<Booking session={self.session_id} client={self.client_id}>"
