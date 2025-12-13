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
