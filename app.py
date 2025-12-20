from flask import Flask, Response, jsonify, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from config import Config
from models import (
    db,
    Producto,
    Cliente,
    Orden,
    OrdenItem,
    Usuario,
    CategoriaProducto,
    MarcaProducto,
    Tienda,
    Talla,
    Client,
    Coach,
    MembershipPlan,
    Membership,
    ClassTemplate,
    ClassSession,
    Booking,
    AccountMovement,
    Payment,
)
from flask_migrate import Migrate
from datetime import datetime, timedelta, date
from flask_cors import CORS
from decimal import Decimal



migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Habilitar CORS para el front (localhost:5173)
    CORS(app, resources={r"/*": {"origins": "*"}})
    # Si quieres permitir cualquier origen durante desarrollo:
    # CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/")
    def index():
        return jsonify({"message": "API funcionando"})

    # ---------- CRUD PRODUCTOS ----------

    @app.route("/productos", methods=["GET"])
    def listar_productos():
        productos = Producto.query.all()
        data = []
        for p in productos:
            data.append({
                "id": p.id,
                "sku": p.sku,

                # Tienda
                "tienda": p.tienda.nombre if p.tienda else None,
                "tienda_id": p.tienda.id if p.tienda else None,

                # Marca
                "marca": p.marca.nombre if p.marca else None,
                "marca_id": p.marca.id if p.marca else None,

                "descripcion": p.descripcion,

                # Categoría
                "categoria": p.categoria.nombre if p.categoria else None,
                "categoria_id": p.categoria.id if p.categoria else None,

                # Talla
                "talla": p.talla.nombre if p.talla else None,
                "talla_id": p.talla.id if p.talla else None,

                "costo": float(p.costo),
                "precio": float(p.precio),
                "cantidad": p.cantidad,
                "imagen": p.imagen,
            })
        return jsonify(data)


    @app.route("/productos/<int:producto_id>", methods=["GET"])
    def obtener_producto(producto_id):
        p = Producto.query.get_or_404(producto_id)
        return jsonify({
            "id": p.id,
            "sku": p.sku,

            "tienda": p.tienda.nombre if p.tienda else None,
            "tienda_id": p.tienda.id if p.tienda else None,

            "marca": p.marca.nombre if p.marca else None,
            "marca_id": p.marca.id if p.marca else None,

            "descripcion": p.descripcion,

            "categoria": p.categoria.nombre if p.categoria else None,
            "categoria_id": p.categoria.id if p.categoria else None,

            "talla": p.talla.nombre if p.talla else None,
            "talla_id": p.talla.id if p.talla else None,

            "costo": float(p.costo),
            "precio": float(p.precio),
            "cantidad": p.cantidad,
            "imagen": p.imagen,
        })


    @app.route("/productos", methods=["POST"])
    def crear_producto():
        data = request.get_json()

        # ===== TIENDA (requerida) =====
        tienda = None
        tienda_id = data.get("tienda_id")
        if tienda_id is not None:
            tienda = Tienda.query.get(tienda_id)
            if not tienda:
                return jsonify({"error": "tienda_id inválido"}), 400
        else:
            tienda_nombre = data.get("tienda")
            if not tienda_nombre:
                return jsonify({"error": "tienda es requerida"}), 400
            tienda = Tienda.query.filter_by(nombre=str(tienda_nombre)).first()
            if not tienda:
                tienda = Tienda(nombre=str(tienda_nombre))
                db.session.add(tienda)
                db.session.flush()

        # ===== MARCA (opcional) =====
        marca = None
        marca_id = data.get("marca_id")
        if marca_id is not None:
            marca = MarcaProducto.query.get(marca_id)
            if not marca:
                return jsonify({"error": "marca_id inválido"}), 400
        else:
            marca_nombre = data.get("marca")
            if marca_nombre:
                marca = MarcaProducto.query.filter_by(nombre=str(marca_nombre)).first()
                if not marca:
                    marca = MarcaProducto(nombre=str(marca_nombre))
                    db.session.add(marca)
                    db.session.flush()

        # ===== CATEGORÍA (opcional) =====
        categoria = None
        categoria_id = data.get("categoria_id")
        if categoria_id is not None:
            categoria = CategoriaProducto.query.get(categoria_id)
            if not categoria:
                return jsonify({"error": "categoria_id inválido"}), 400
        else:
            categoria_nombre = data.get("categoria")
            if categoria_nombre:
                categoria = CategoriaProducto.query.filter_by(nombre=str(categoria_nombre)).first()
                if not categoria:
                    categoria = CategoriaProducto(nombre=str(categoria_nombre))
                    db.session.add(categoria)
                    db.session.flush()

        # ===== TALLA (opcional) =====
        talla = None
        talla_id = data.get("talla_id")
        if talla_id is not None:
            talla = Talla.query.get(talla_id)
            if not talla:
                return jsonify({"error": "talla_id inválido"}), 400
        else:
            talla_nombre = data.get("talla")
            if talla_nombre:
                talla = Talla.query.filter_by(nombre=str(talla_nombre)).first()
                if not talla:
                    talla = Talla(nombre=str(talla_nombre))
                    db.session.add(talla)
                    db.session.flush()

        # ===== PRODUCTO =====
        # sku es opcional
        sku = data.get("sku")

        try:
            descripcion = data["descripcion"]
            costo = data["costo"]
            precio = data["precio"]
        except KeyError as e:
            return jsonify({"error": f"campo requerido faltante: {e.args[0]}"}), 400

        p = Producto(
            sku=sku,
            tienda=tienda,
            marca=marca,
            categoria=categoria,
            talla=talla,
            descripcion=descripcion,
            costo=costo,
            precio=precio,
            cantidad=data.get("cantidad", 0),
            imagen=data.get("imagen"),
        )

        db.session.add(p)
        db.session.commit()

        return jsonify({"id": p.id}), 201


    @app.route("/productos/<int:producto_id>", methods=["PUT", "PATCH"])
    def actualizar_producto(producto_id):
        p = Producto.query.get_or_404(producto_id)
        data = request.get_json()

        # SKU
        if "sku" in data:
            p.sku = data["sku"]

        # Descripción
        if "descripcion" in data:
            p.descripcion = data["descripcion"]

        # TIENDA
        if "tienda_id" in data:
            tienda = Tienda.query.get(data["tienda_id"])
            if not tienda:
                return jsonify({"error": "tienda_id inválido"}), 400
            p.tienda = tienda
        elif "tienda" in data:
            tienda_nombre = data.get("tienda")
            if tienda_nombre:
                tienda = Tienda.query.filter_by(nombre=tienda_nombre).first()
                if not tienda:
                    tienda = Tienda(nombre=tienda_nombre)
                    db.session.add(tienda)
                    db.session.flush()
                p.tienda = tienda

        # MARCA
        if "marca_id" in data:
            marca_id = data.get("marca_id")
            if marca_id is None:
                p.marca = None
            else:
                m = MarcaProducto.query.get(marca_id)
                if not m:
                    return jsonify({"error": "marca_id inválido"}), 400
                p.marca = m
        elif "marca" in data:
            marca_nombre = data.get("marca")
            if marca_nombre:
                m = MarcaProducto.query.filter_by(nombre=marca_nombre).first()
                if not m:
                    m = MarcaProducto(nombre=marca_nombre)
                    db.session.add(m)
                    db.session.flush()
                p.marca = m
            else:
                p.marca = None

        # CATEGORÍA
        if "categoria_id" in data:
            categoria_id = data.get("categoria_id")
            if categoria_id is None:
                p.categoria = None
            else:
                cat = CategoriaProducto.query.get(categoria_id)
                if not cat:
                    return jsonify({"error": "categoria_id inválido"}), 400
                p.categoria = cat
        elif "categoria" in data:
            categoria_nombre = data.get("categoria")
            if categoria_nombre:
                cat = CategoriaProducto.query.filter_by(nombre=categoria_nombre).first()
                if not cat:
                    cat = CategoriaProducto(nombre=categoria_nombre)
                    db.session.add(cat)
                    db.session.flush()
                p.categoria = cat
            else:
                p.categoria = None

        # TALLA (opcional)
        if "talla_id" in data:
            talla_id = data.get("talla_id")
            if talla_id is None:
                p.talla = None
            else:
                t = Talla.query.get(talla_id)
                if not t:
                    return jsonify({"error": "talla_id inválido"}), 400
                p.talla = t
        elif "talla" in data:
            talla_nombre = data.get("talla")
            if talla_nombre:
                t = Talla.query.filter_by(nombre=talla_nombre).first()
                if not t:
                    t = Talla(nombre=talla_nombre)
                    db.session.add(t)
                    db.session.flush()
                p.talla = t
            else:
                p.talla = None

        # Campos numéricos / otros
        if "costo" in data:
            p.costo = data["costo"]
        if "precio" in data:
            p.precio = data["precio"]
        if "cantidad" in data:
            p.cantidad = data["cantidad"]
        if "imagen" in data:
            p.imagen = data["imagen"]

        db.session.commit()

        return jsonify({"message": "Producto actualizado"})


    @app.route("/productos/<int:producto_id>", methods=["DELETE"])
    def eliminar_producto(producto_id):
        p = Producto.query.get_or_404(producto_id)
        db.session.delete(p)
        db.session.commit()
        return jsonify({"message": "Producto eliminado"})

    

    from datetime import datetime

    def parse_iso_datetime(value: str) -> datetime:
        """
        Convierte una cadena ISO 8601 a datetime.
        Acepta 'Z' al final como UTC.
        """
        if not value:
            return None
        # si termina en 'Z', lo cambiamos a +00:00
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)

    def parse_iso_date(value: str):
        if not value:
            return None
        return datetime.fromisoformat(value).date()

    def parse_time(value: str):
        if not value:
            return None
        # acepta "HH:MM" o "HH:MM:SS"
        fmt = "%H:%M:%S" if value.count(":") == 2 else "%H:%M"
        return datetime.strptime(value, fmt).time()

    def get_client_balance(client_id: int):
        client = Client.query.get(client_id)
        if not client:
            return None
        return float(client.saldo or 0)

    def apply_movement_and_update_balance(client: Client, movement: AccountMovement):
        current_saldo = Decimal(str(client.saldo or 0))
        delta = Decimal(str(movement.amount or 0))
        client.saldo = current_saldo + delta
        db.session.add(movement)
        db.session.add(client)

    def calcular_subtotal_items(items):
        return sum((item.cantidad or 0) * (item.precio_unitario or 0) for item in items)

    # Helper para serializar una orden completa
    def orden_to_dict(orden: Orden):
        return {
            "id": orden.id,
            "codigo": orden.codigo,
            "fecha": orden.fecha.isoformat(),
            "descuento": float(orden.descuento) if orden.descuento is not None else 0,
            "total": float(orden.total) if orden.total is not None else 0,
            "cliente": {
                "id": orden.cliente.id,
                "nombre": orden.cliente.nombre,
                "telefono": orden.cliente.telefono,
                "email": orden.cliente.email,
                "nit": orden.cliente.nit,
            },
            "items": [
                {
                    "id": item.id,
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "precio_unitario": float(item.precio_unitario),
                    # 🔹 info básica del producto (sin meter objetos crudos)
                    "producto": {
                        "id": item.producto.id,
                        "descripcion": item.producto.descripcion,
                        "sku": item.producto.sku,
                        "tienda_id": item.producto.tienda_id,
                        "tienda": item.producto.tienda.nombre if item.producto.tienda else None,
                        "marca": item.producto.marca.nombre if item.producto.marca else None,
                        "categoria": item.producto.categoria.nombre if item.producto.categoria else None,
                        "talla_id": item.producto.talla_id,
                        "talla": item.producto.talla.nombre if item.producto.talla else None,
                        "costo": float(item.producto.costo) if item.producto and item.producto.costo is not None else None,
                    } if item.producto else None,
                }
                for item in orden.items
            ],
        }



    # ---------- CRUD ORDENES ----------

    @app.route("/ordenes", methods=["GET"])
    def listar_ordenes():
        """
        Lista órdenes, opcionalmente filtradas por rango de fechas.

        Query params:
        - inicio: fecha/hora ISO 8601 (ej: 2025-11-01T00:00:00Z)
        - fin:    fecha/hora ISO 8601 (ej: 2025-11-30T23:59:59Z)

        Ejemplos:
        GET /ordenes
        GET /ordenes?inicio=2025-11-01T00:00:00Z&fin=2025-11-30T23:59:59Z
        """
        inicio_str = request.args.get("inicio")
        fin_str = request.args.get("fin")

        query = Orden.query

        # Filtro fecha inicio
        if inicio_str:
            try:
                inicio = parse_iso_datetime(inicio_str)
            except Exception:
                return jsonify({"error": "parametro 'inicio' debe estar en formato ISO 8601"}), 400
            query = query.filter(Orden.fecha >= inicio)

        # Filtro fecha fin
        if fin_str:
            try:
                fin = parse_iso_datetime(fin_str)
            except Exception:
                return jsonify({"error": "parametro 'fin' debe estar en formato ISO 8601"}), 400
            query = query.filter(Orden.fecha <= fin)

        ordenes = query.order_by(Orden.fecha.desc()).all()
        data = [orden_to_dict(o) for o in ordenes]
        return jsonify(data)


    @app.route("/ordenes/<int:orden_id>", methods=["GET"])
    def obtener_orden(orden_id):
        orden = Orden.query.get_or_404(orden_id)
        return jsonify(orden_to_dict(orden))


    @app.route("/ordenes", methods=["POST"])
    def crear_orden():
        """
        Crea una nueva orden.

        Espera un JSON tipo:

        {
        "codigo": "ORD-001",
        "fecha": "2025-11-10T10:10:00Z",   // opcional
        "cliente": {
            "id": 1                      // OPCIÓN 1: cliente existente
        }
        // O bien:
        // "cliente": {
        //   "nombre": "Ana López",     // OPCIÓN 2: crear/buscar por datos
        //   "telefono": "+502 5555 1111"
        // },
        "items": [
            { "producto_id": 1, "cantidad": 2, "precio_unitario": 250 },
            { "producto_id": 3, "cantidad": 1, "precio_unitario": 400 }
        ]
        }
        """
        data = request.get_json()

        # 1) Cliente
        cliente_data = data.get("cliente")
        if not cliente_data:
            return jsonify({"error": "cliente es requerido"}), 400

        cliente = None

        # Si viene cliente.id, usamos cliente existente
        if "id" in cliente_data:
            cliente = Cliente.query.get(cliente_data["id"])
            if not cliente:
                return jsonify({"error": "cliente con ese id no existe"}), 400
        else:
            # Buscamos por telefono (y/o nombre). Si no existe, lo creamos.
            nombre = cliente_data.get("nombre")
            telefono = cliente_data.get("telefono")
            email = cliente_data.get("email")
            nit = cliente_data.get("nit")

            if not nombre or not telefono:
                return jsonify({"error": "cliente requiere nombre y telefono"}), 400

            cliente = Cliente.query.filter_by(telefono=telefono).first()
            if not cliente:
                cliente = Cliente(
                    nombre=nombre.strip(),
                    telefono=telefono.strip(),
                    email=email.strip() if isinstance(email, str) else email,
                    nit=nit.strip() if isinstance(nit, str) else nit,
                )
                db.session.add(cliente)

        # 2) Orden
        codigo = data.get("codigo")
        if not codigo:
            return jsonify({"error": "codigo de orden es requerido"}), 400

        fecha_str = data.get("fecha")
        fecha = parse_iso_datetime(fecha_str) if fecha_str else datetime.utcnow()

        orden = Orden(
            codigo=codigo,
            fecha=fecha,
            cliente=cliente
        )
        db.session.add(orden)
        db.session.flush()  # para tener orden.id

        # 3) Items (solo productos)
        items_data = data.get("items", [])
        if not items_data:
            return jsonify({"error": "debe incluir al menos un item en 'items'"}), 400

        subtotal = 0
        for item_data in items_data:
            cantidad = item_data.get("cantidad", 1)
            precio_unitario = item_data.get("precio_unitario")

            if precio_unitario is None:
                return jsonify({"error": "precio_unitario es requerido en cada item"}), 400

            producto_id = item_data.get("producto_id")
            if not producto_id:
                return jsonify({"error": "producto_id es requerido en cada item"}), 400

            producto = Producto.query.get(producto_id)
            if not producto:
                return jsonify({"error": f"producto {producto_id} no existe"}), 400

            # Descontar inventario (se permite negativo)
            producto.cantidad = (producto.cantidad or 0) - cantidad
            subtotal += cantidad * precio_unitario

            orden_item = OrdenItem(
                orden=orden,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
            )
            db.session.add(orden_item)

        descuento_val = data.get("descuento", 0) or 0
        total_val = data.get("total")
        orden.descuento = descuento_val
        orden.total = total_val if total_val is not None else subtotal - float(descuento_val)

        db.session.commit()

        return jsonify(orden_to_dict(orden)), 201


    @app.route("/ordenes/<int:orden_id>", methods=["PUT", "PATCH"])
    def actualizar_orden(orden_id):
        """
        Actualiza una orden.

        Permite actualizar:
        - codigo
        - fecha
        - cliente (solo por id)
        - items (si se envía 'items', se reemplazan todos los items)
        """
        orden = Orden.query.get_or_404(orden_id)
        data = request.get_json()

        descuento_val = orden.descuento if orden.descuento is not None else 0

        if "codigo" in data:
            orden.codigo = data["codigo"]

        if "fecha" in data:
            orden.fecha = parse_iso_datetime(data["fecha"])

        # Cliente (solo permitimos cambiar cliente por id para simplificar)
        if "cliente_id" in data:
            cliente = Cliente.query.get(data["cliente_id"])
            if not cliente:
                return jsonify({"error": "cliente_id no válido"}), 400
            orden.cliente = cliente

        if "descuento" in data:
            descuento_val = data.get("descuento", 0) or 0
            orden.descuento = descuento_val

        total_payload = data.get("total") if "total" in data else None

        # Reemplazar items si viene "items"
        if "items" in data:
            # Revertir inventario de los items actuales y borrarlos
            for item in list(orden.items):
                if item.producto:
                    item.producto.cantidad = (item.producto.cantidad or 0) + item.cantidad
                db.session.delete(item)
            db.session.flush()

            items_data = data["items"]
            subtotal = 0
            for item_data in items_data:
                cantidad = item_data.get("cantidad", 1)
                precio_unitario = item_data.get("precio_unitario")

                if precio_unitario is None:
                    return jsonify({"error": "precio_unitario es requerido en cada item"}), 400

                producto_id = item_data.get("producto_id")
                if not producto_id:
                    return jsonify({"error": "producto_id es requerido en cada item"}), 400

                producto = Producto.query.get(producto_id)
                if not producto:
                    return jsonify({"error": f"producto {producto_id} no existe"}), 400

                # Descontar inventario (se permite negativo)
                producto.cantidad = (producto.cantidad or 0) - cantidad
                subtotal += cantidad * precio_unitario

                orden_item = OrdenItem(
                    orden=orden,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                )
                db.session.add(orden_item)

            orden.total = total_payload if total_payload is not None else subtotal - float(descuento_val)
        else:
            if "total" in data:
                orden.total = total_payload
            elif "descuento" in data:
                subtotal_actual = calcular_subtotal_items(orden.items)
                orden.total = subtotal_actual - float(descuento_val)

        db.session.commit()
        return jsonify(orden_to_dict(orden))


    @app.route("/ordenes/<int:orden_id>", methods=["DELETE"])
    def eliminar_orden(orden_id):
        orden = Orden.query.get_or_404(orden_id)
        db.session.delete(orden)
        db.session.commit()
        return jsonify({"message": "Orden eliminada"})


        # ---------- CRUD USUARIOS ----------

    @app.route("/usuarios", methods=["GET"])
    def listar_usuarios():
        """
        Lista todos los usuarios.
        No devolvemos password_hash por seguridad.
        """
        usuarios = Usuario.query.all()
        data = [
            {
                "id": u.id,
                "username": u.username,
                "is_admin": u.is_admin,
                "creado_en": u.creado_en.isoformat(),
            }
            for u in usuarios
        ]
        return jsonify(data)

    @app.route("/usuarios/<int:usuario_id>", methods=["GET"])
    def obtener_usuario(usuario_id):
        """
        Retorna un usuario específico.
        """
        u = Usuario.query.get_or_404(usuario_id)
        return jsonify({
            "id": u.id,
            "username": u.username,
            "is_admin": u.is_admin,
            "creado_en": u.creado_en.isoformat(),
        })

    @app.route("/usuarios", methods=["POST"])
    def crear_usuario():
        """
        Crea un usuario nuevo.

        Espera JSON:
        {
        "username": "ana",
        "password": "mi_contrasena_segura",
        "is_admin": true   // opcional, default false
        }
        """
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        is_admin = data.get("is_admin", False)

        if not username or not password:
            return jsonify({"error": "username y password son requeridos"}), 400

        # Verificar que no exista ya
        if Usuario.query.filter_by(username=username).first():
            return jsonify({"error": "username ya existe"}), 400

        usuario = Usuario(
            username=username,
            is_admin=is_admin
        )
        usuario.set_password(password)

        db.session.add(usuario)
        db.session.commit()

        return jsonify({
            "id": usuario.id,
            "username": usuario.username,
            "is_admin": usuario.is_admin,
            "creado_en": usuario.creado_en.isoformat(),
        }), 201

    @app.route("/usuarios/<int:usuario_id>", methods=["PUT", "PATCH"])
    def actualizar_usuario(usuario_id):
        """
        Actualiza datos del usuario.

        Puedes mandar cualquiera de:
        {
        "username": "nuevo_nombre",
        "password": "nueva_contrasena",
        "is_admin": true/false
        }
        """
        usuario = Usuario.query.get_or_404(usuario_id)
        data = request.get_json()

        if "username" in data:
            nuevo_username = data["username"]
            if nuevo_username != usuario.username:
                # Revisar que no se repita
                if Usuario.query.filter_by(username=nuevo_username).first():
                    return jsonify({"error": "username ya existe"}), 400
                usuario.username = nuevo_username

        if "password" in data and data["password"]:
            usuario.set_password(data["password"])

        if "is_admin" in data:
            usuario.is_admin = bool(data["is_admin"])

        db.session.commit()

        return jsonify({
            "id": usuario.id,
            "username": usuario.username,
            "is_admin": usuario.is_admin,
            "creado_en": usuario.creado_en.isoformat(),
        })

    @app.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
    def eliminar_usuario(usuario_id):
        """
        Elimina un usuario.
        (Más adelante puedes agregar lógica para no borrar el último admin, etc.)
        """
        usuario = Usuario.query.get_or_404(usuario_id)
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"message": "Usuario eliminado"})

    @app.route("/auth/login", methods=["POST"])
    def login():
        """
        Login básico.

        Espera JSON:
        {
        "username": "ana",
        "password": "mi_contrasena"
        }

        Responde 200 si las credenciales son correctas,
        401 si no.
        """
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "username y password son requeridos"}), 400

        usuario = Usuario.query.filter_by(username=username).first()
        if not usuario or not usuario.check_password(password):
            return jsonify({"error": "credenciales inválidas"}), 401

        # Más adelante aquí podrías devolver un JWT o sesión.
        return jsonify({
            "id": usuario.id,
            "username": usuario.username,
            "is_admin": usuario.is_admin
        })
    
    # ---------- CRUD CATEGORIAS PRODUCTOS ----------

    @app.route("/categorias-productos", methods=["GET"])
    def listar_categorias_productos():
        categorias = CategoriaProducto.query.order_by(CategoriaProducto.nombre).all()
        return jsonify([
            {
                "id": c.id,
                "nombre": c.nombre,
                "descripcion": c.descripcion,
                "activo": c.activo,
            }
            for c in categorias
        ])


    @app.route("/categorias-productos", methods=["POST"])
    def crear_categoria_producto():
        data = request.get_json()
        nombre = data.get("nombre")
        if not nombre:
            return jsonify({"error": "nombre es requerido"}), 400

        if CategoriaProducto.query.filter_by(nombre=nombre).first():
            return jsonify({"error": "ya existe una categoría con ese nombre"}), 400

        c = CategoriaProducto(
            nombre=nombre,
            descripcion=data.get("descripcion"),
            activo=data.get("activo", True),
        )
        db.session.add(c)
        db.session.commit()
        return jsonify({"id": c.id}), 201


    @app.route("/categorias-productos/<int:cat_id>", methods=["PUT", "PATCH"])
    def actualizar_categoria_producto(cat_id):
        c = CategoriaProducto.query.get_or_404(cat_id)
        data = request.get_json()

        if "nombre" in data:
            nuevo = data["nombre"]
            if nuevo != c.nombre and CategoriaProducto.query.filter_by(nombre=nuevo).first():
                return jsonify({"error": "ya existe una categoría con ese nombre"}), 400
            c.nombre = nuevo

        if "descripcion" in data:
            c.descripcion = data["descripcion"]

        if "activo" in data:
            c.activo = bool(data["activo"])

        db.session.commit()
        return jsonify({"message": "Categoría de producto actualizada"})


    @app.route("/categorias-productos/<int:cat_id>", methods=["DELETE"])
    def eliminar_categoria_producto(cat_id):
        c = CategoriaProducto.query.get_or_404(cat_id)
        db.session.delete(c)
        db.session.commit()
        return jsonify({"message": "Categoría de producto eliminada"})


    # ---------- CRUD MARCAS PRODUCTOS ----------

    @app.route("/marcas-productos", methods=["GET"])
    def listar_marcas_productos():
        marcas = MarcaProducto.query.order_by(MarcaProducto.nombre).all()
        return jsonify([
            {
                "id": m.id,
                "nombre": m.nombre,
                "descripcion": m.descripcion,
                "activo": m.activo,
            }
            for m in marcas
        ])


    @app.route("/marcas-productos", methods=["POST"])
    def crear_marca_producto():
        data = request.get_json()
        nombre = data.get("nombre")
        if not nombre:
            return jsonify({"error": "nombre es requerido"}), 400

        if MarcaProducto.query.filter_by(nombre=nombre).first():
            return jsonify({"error": "ya existe una marca con ese nombre"}), 400

        m = MarcaProducto(
            nombre=nombre,
            descripcion=data.get("descripcion"),
            activo=data.get("activo", True),
        )
        db.session.add(m)
        db.session.commit()
        return jsonify({"id": m.id}), 201


    @app.route("/marcas-productos/<int:marca_id>", methods=["PUT", "PATCH"])
    def actualizar_marca_producto(marca_id):
        m = MarcaProducto.query.get_or_404(marca_id)
        data = request.get_json()

        if "nombre" in data:
            nuevo = data["nombre"]
            if nuevo != m.nombre and MarcaProducto.query.filter_by(nombre=nuevo).first():
                return jsonify({"error": "ya existe una marca con ese nombre"}), 400
            m.nombre = nuevo

        if "descripcion" in data:
            m.descripcion = data["descripcion"]

        if "activo" in data:
            m.activo = bool(data["activo"])

        db.session.commit()
        return jsonify({"message": "Marca de producto actualizada"})


    @app.route("/marcas-productos/<int:marca_id>", methods=["DELETE"])
    def eliminar_marca_producto(marca_id):
        m = MarcaProducto.query.get_or_404(marca_id)
        db.session.delete(m)
        db.session.commit()
        return jsonify({"message": "Marca de producto eliminada"})


    # =========================
    # CRUD CLIENTES
    # =========================

    @app.route("/clientes", methods=["GET"])
    def listar_clientes():
        """
        Lista todos los clientes.
        Opcional: ?q=texto para filtrar por nombre (para el Autocomplete).
        """
        q = request.args.get("q", type=str)

        query = Cliente.query
        if q:
            # filtra por nombre que contenga 'q' (case-insensitive)
            like = f"%{q}%"
            query = query.filter(Cliente.nombre.ilike(like))

        clientes = query.order_by(Cliente.nombre.asc()).all()

        return jsonify([
            {
                "id": c.id,
                "nombre": c.nombre,
                "telefono": c.telefono,
                "email": c.email,
                "nit": c.nit,
            }
            for c in clientes
        ]), 200


    @app.route("/clientes/<int:cliente_id>", methods=["GET"])
    def obtener_cliente(cliente_id):
        """
        Obtener un cliente por ID.
        """
        cliente = Cliente.query.get_or_404(cliente_id)
        return jsonify({
            "id": cliente.id,
            "nombre": cliente.nombre,
            "telefono": cliente.telefono,
            "email": cliente.email,
            "nit": cliente.nit,
        }), 200


    @app.route("/clientes", methods=["POST"])
    def crear_cliente():
        """
        Crear un nuevo cliente.
        Body JSON:
        {
        "nombre": "Ana López",
        "telefono": "+502 5555 1111",
        "email": "ana@example.com",   // opcional
        "nit": "123456-7"             // opcional
        }
        """
        data = request.get_json() or {}

        nombre = data.get("nombre")
        telefono = data.get("telefono")
        email = data.get("email")
        nit = data.get("nit")

        if not nombre or not telefono:
            return jsonify({"error": "nombre y telefono son obligatorios"}), 400

        nuevo = Cliente(
            nombre=nombre.strip(),
            telefono=telefono.strip(),
            email=email.strip() if isinstance(email, str) else email,
            nit=nit.strip() if isinstance(nit, str) else nit,
        )
        db.session.add(nuevo)
        db.session.commit()

        return jsonify({
            "id": nuevo.id,
            "nombre": nuevo.nombre,
            "telefono": nuevo.telefono,
            "email": nuevo.email,
            "nit": nuevo.nit,
        }), 201


    @app.route("/clientes/<int:cliente_id>", methods=["PUT", "PATCH"])
    def actualizar_cliente(cliente_id):
        """
        Actualizar un cliente existente.
        Body JSON (campos opcionales):
        {
        "nombre": "Nuevo nombre",
        "telefono": "Nuevo teléfono",
        "email": "nuevo@example.com",
        "nit": "987654-3"
        }
        """
        cliente = Cliente.query.get_or_404(cliente_id)
        data = request.get_json() or {}

        nombre = data.get("nombre")
        telefono = data.get("telefono")
        email = data.get("email")
        nit = data.get("nit")

        if nombre is not None:
            cliente.nombre = nombre.strip()

        if telefono is not None:
            cliente.telefono = telefono.strip()

        if email is not None:
            cliente.email = email.strip() if isinstance(email, str) else email

        if nit is not None:
            cliente.nit = nit.strip() if isinstance(nit, str) else nit

        db.session.commit()

        return jsonify({
            "id": cliente.id,
            "nombre": cliente.nombre,
            "telefono": cliente.telefono,
            "email": cliente.email,
            "nit": cliente.nit,
        }), 200


    @app.route("/clientes/<int:cliente_id>", methods=["DELETE"])
    def eliminar_cliente(cliente_id):
        """
        Eliminar un cliente.
        Opcional: podrías evitar borrar si tiene órdenes asociadas.
        """
        cliente = Cliente.query.get_or_404(cliente_id)

        # Si quieres evitar borrar clientes con órdenes:
        # if cliente.ordenes and len(cliente.ordenes) > 0:
        #     return jsonify({"error": "No se puede eliminar un cliente con órdenes asociadas"}), 400

        db.session.delete(cliente)
        db.session.commit()

        return jsonify({"message": "Cliente eliminado correctamente"}), 200

    # ---------- CRUD TIENDAS ----------

    @app.route("/tiendas", methods=["GET"])
    def listar_tiendas():
        tiendas = Tienda.query.order_by(Tienda.nombre.asc()).all()
        data = [
            {
                "id": t.id,
                "nombre": t.nombre,
                "descripcion": t.descripcion,
                "activo": t.activo,
            }
            for t in tiendas
        ]
        return jsonify(data)


    @app.route("/tiendas/<int:tienda_id>", methods=["GET"])
    def obtener_tienda(tienda_id):
        t = Tienda.query.get_or_404(tienda_id)
        return jsonify({
            "id": t.id,
            "nombre": t.nombre,
            "descripcion": t.descripcion,
            "activo": t.activo,
        })


    @app.route("/tiendas", methods=["POST"])
    def crear_tienda():
        data = request.get_json() or {}
        nombre = data.get("nombre")
        descripcion = data.get("descripcion")

        if not nombre:
            return jsonify({"error": "nombre es requerido"}), 400

        # opcional: evitar duplicados por nombre
        existente = Tienda.query.filter_by(nombre=nombre).first()
        if existente:
            return jsonify({"error": "ya existe una tienda con ese nombre"}), 400

        t = Tienda(
            nombre=nombre,
            descripcion=descripcion,
        )
        db.session.add(t)
        db.session.commit()

        return jsonify({
            "id": t.id,
            "nombre": t.nombre,
            "descripcion": t.descripcion,
            "activo": t.activo,
        }), 201


    @app.route("/tiendas/<int:tienda_id>", methods=["PUT", "PATCH"])
    def actualizar_tienda(tienda_id):
        t = Tienda.query.get_or_404(tienda_id)
        data = request.get_json() or {}

        if "nombre" in data:
            t.nombre = data["nombre"]
        if "descripcion" in data:
            t.descripcion = data["descripcion"]
        if "activo" in data:
            t.activo = bool(data["activo"])

        db.session.commit()

        return jsonify({
            "id": t.id,
            "nombre": t.nombre,
            "descripcion": t.descripcion,
            "activo": t.activo,
        })


    @app.route("/tiendas/<int:tienda_id>", methods=["DELETE"])
    def eliminar_tienda(tienda_id):
        t = Tienda.query.get_or_404(tienda_id)
        db.session.delete(t)
        db.session.commit()
        return jsonify({"message": "Tienda eliminada"})
    

    # ---------- CRUD TALLAS ----------

    @app.route("/tallas", methods=["GET"])
    def listar_tallas():
        tallas = Talla.query.order_by(Talla.nombre.asc()).all()
        data = [
            {
                "id": ta.id,
                "nombre": ta.nombre,
                "descripcion": ta.descripcion,
                "activo": ta.activo,
            }
            for ta in tallas
        ]
        return jsonify(data)


    @app.route("/tallas/<int:talla_id>", methods=["GET"])
    def obtener_talla(talla_id):
        ta = Talla.query.get_or_404(talla_id)
        return jsonify({
            "id": ta.id,
            "nombre": ta.nombre,
            "descripcion": ta.descripcion,
            "activo": ta.activo,
        })


    @app.route("/tallas", methods=["POST"])
    def crear_talla():
        data = request.get_json() or {}
        nombre = data.get("nombre")
        descripcion = data.get("descripcion")

        if not nombre:
            return jsonify({"error": "nombre es requerido"}), 400

        # opcional: evitar duplicados
        existente = Talla.query.filter_by(nombre=nombre).first()
        if existente:
            return jsonify({"error": "ya existe una talla con ese nombre"}), 400

        ta = Talla(
            nombre=nombre,
            descripcion=descripcion,
        )
        db.session.add(ta)
        db.session.commit()

        return jsonify({
            "id": ta.id,
            "nombre": ta.nombre,
            "descripcion": ta.descripcion,
            "activo": ta.activo,
        }), 201


    @app.route("/tallas/<int:talla_id>", methods=["PUT", "PATCH"])
    def actualizar_talla(talla_id):
        ta = Talla.query.get_or_404(talla_id)
        data = request.get_json() or {}

        if "nombre" in data:
            ta.nombre = data["nombre"]
        if "descripcion" in data:
            ta.descripcion = data["descripcion"]
        if "activo" in data:
            ta.activo = bool(data["activo"])

        db.session.commit()

        return jsonify({
            "id": ta.id,
            "nombre": ta.nombre,
            "descripcion": ta.descripcion,
            "activo": ta.activo,
        })


    @app.route("/tallas/<int:talla_id>", methods=["DELETE"])
    def eliminar_talla(talla_id):
        ta = Talla.query.get_or_404(talla_id)
        db.session.delete(ta)
        db.session.commit()
        return jsonify({"message": "Talla eliminada"})

    # ---------- CRUD CLIENTS (nuevo módulo) ----------

    @app.route("/clients", methods=["GET"])
    def list_clients():
        records = Client.query.order_by(Client.nombre.asc()).all()
        return jsonify([c.to_dict() for c in records])

    @app.route("/clients/<int:client_id>", methods=["GET"])
    def get_client(client_id):
        c = Client.query.get_or_404(client_id)
        return jsonify(c.to_dict())

    @app.route("/clients", methods=["POST"])
    def create_client():
        data = request.get_json() or {}
        nombre = data.get("nombre")
        telefono = data.get("telefono")
        if not nombre or not telefono:
            return jsonify({"error": "nombre y telefono son requeridos"}), 400
        c = Client(
            nombre=nombre.strip(),
            telefono=telefono.strip(),
            email=data.get("email"),
            activo=data.get("activo", True),
        )
        db.session.add(c)
        db.session.commit()
        return jsonify({"id": c.id}), 201

    @app.route("/clients/<int:client_id>", methods=["PUT", "PATCH"])
    def update_client(client_id):
        c = Client.query.get_or_404(client_id)
        data = request.get_json() or {}
        if "nombre" in data:
            c.nombre = data["nombre"]
        if "telefono" in data:
            c.telefono = data["telefono"]
        if "email" in data:
            c.email = data["email"]
        if "activo" in data:
            c.activo = bool(data["activo"])
        db.session.commit()
        return jsonify(c.to_dict())

    @app.route("/clients/<int:client_id>", methods=["DELETE"])
    def delete_client(client_id):
        c = Client.query.get_or_404(client_id)
        db.session.delete(c)
        db.session.commit()
        return jsonify({"message": "Client eliminado"})

    @app.route("/clients/<int:client_id>/balance", methods=["GET"])
    def get_client_balance_route(client_id):
        c = Client.query.get_or_404(client_id)
        return jsonify({
            "client_id": c.id,
            "saldo": float(c.saldo or 0),
        })

    # ---------- CRUD COACHES ----------

    @app.route("/coaches", methods=["GET"])
    def list_coaches():
        records = Coach.query.order_by(Coach.nombre.asc()).all()
        return jsonify([c.to_dict() for c in records])

    @app.route("/coaches/<int:coach_id>", methods=["GET"])
    def get_coach(coach_id):
        c = Coach.query.get_or_404(coach_id)
        return jsonify(c.to_dict())

    @app.route("/coaches", methods=["POST"])
    def create_coach():
        data = request.get_json() or {}
        nombre = data.get("nombre")
        telefono = data.get("telefono")
        if not nombre or not telefono:
            return jsonify({"error": "nombre y telefono son requeridos"}), 400
        c = Coach(
            nombre=nombre.strip(),
            telefono=telefono.strip(),
            email=data.get("email"),
            activo=data.get("activo", True),
        )
        db.session.add(c)
        db.session.commit()
        return jsonify({"id": c.id}), 201

    @app.route("/coaches/<int:coach_id>", methods=["PUT", "PATCH"])
    def update_coach(coach_id):
        c = Coach.query.get_or_404(coach_id)
        data = request.get_json() or {}
        if "nombre" in data:
            c.nombre = data["nombre"]
        if "telefono" in data:
            c.telefono = data["telefono"]
        if "email" in data:
            c.email = data["email"]
        if "activo" in data:
            c.activo = bool(data["activo"])
        db.session.commit()
        return jsonify(c.to_dict())

    @app.route("/coaches/<int:coach_id>", methods=["DELETE"])
    def delete_coach(coach_id):
        c = Coach.query.get_or_404(coach_id)
        db.session.delete(c)
        db.session.commit()
        return jsonify({"message": "Coach eliminado"})

    # ---------- CRUD MEMBERSHIP PLANS ----------

    @app.route("/membership-plans", methods=["GET"])
    def list_membership_plans():
        records = MembershipPlan.query.order_by(MembershipPlan.nombre.asc()).all()
        return jsonify([p.to_dict() for p in records])

    @app.route("/membership-plans/<int:plan_id>", methods=["GET"])
    def get_membership_plan(plan_id):
        p = MembershipPlan.query.get_or_404(plan_id)
        return jsonify(p.to_dict())

    @app.route("/membership-plans", methods=["POST"])
    def create_membership_plan():
        data = request.get_json() or {}
        nombre = data.get("nombre")
        precio = data.get("precio")
        if not nombre or precio is None:
            return jsonify({"error": "nombre y precio son requeridos"}), 400
        p = MembershipPlan(
            nombre=nombre,
            max_clases_por_semana=data.get("max_clases_por_semana"),
            max_clases_totales=data.get("max_clases_totales"),
            duracion_dias=data.get("duracion_dias"),
            precio=precio,
            activo=data.get("activo", True),
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({"id": p.id}), 201

    @app.route("/membership-plans/<int:plan_id>", methods=["PUT", "PATCH"])
    def update_membership_plan(plan_id):
        p = MembershipPlan.query.get_or_404(plan_id)
        data = request.get_json() or {}
        if "nombre" in data:
            p.nombre = data["nombre"]
        if "max_clases_por_semana" in data:
            p.max_clases_por_semana = data["max_clases_por_semana"]
        if "max_clases_totales" in data:
            p.max_clases_totales = data["max_clases_totales"]
        if "duracion_dias" in data:
            p.duracion_dias = data["duracion_dias"]
        if "precio" in data:
            p.precio = data["precio"]
        if "activo" in data:
            p.activo = bool(data["activo"])
        db.session.commit()
        return jsonify(p.to_dict())

    @app.route("/membership-plans/<int:plan_id>", methods=["DELETE"])
    def delete_membership_plan(plan_id):
        p = MembershipPlan.query.get_or_404(plan_id)
        db.session.delete(p)
        db.session.commit()
        return jsonify({"message": "MembershipPlan eliminado"})

    # ---------- CRUD MEMBERSHIPS ----------

    @app.route("/memberships", methods=["GET"])
    def list_memberships():
        records = Membership.query.all()
        return jsonify([m.to_dict() for m in records])

    @app.route("/memberships/<int:membership_id>", methods=["GET"])
    def get_membership(membership_id):
        m = Membership.query.get_or_404(membership_id)
        return jsonify(m.to_dict())

    @app.route("/memberships", methods=["POST"])
    def create_membership():
        data = request.get_json() or {}
        try:
            client_id = data["client_id"]
            plan_id = data["plan_id"]
            fecha_inicio = parse_iso_date(data["fecha_inicio"])
            fecha_fin = parse_iso_date(data["fecha_fin"])
            estado = data["estado"]
        except KeyError as e:
            return jsonify({"error": f"falta campo requerido {e.args[0]}"}), 400

        if not Client.query.get(client_id):
            return jsonify({"error": "client_id no válido"}), 400
        if not MembershipPlan.query.get(plan_id):
            return jsonify({"error": "plan_id no válido"}), 400

        m = Membership(
            client_id=client_id,
            plan_id=plan_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado,
            clases_usadas=data.get("clases_usadas", 0),
        )
        db.session.add(m)
        db.session.commit()
        return jsonify({"id": m.id}), 201

    @app.route("/memberships/<int:membership_id>", methods=["PUT", "PATCH"])
    def update_membership(membership_id):
        m = Membership.query.get_or_404(membership_id)
        data = request.get_json() or {}
        if "client_id" in data:
            if not Client.query.get(data["client_id"]):
                return jsonify({"error": "client_id no válido"}), 400
            m.client_id = data["client_id"]
        if "plan_id" in data:
            if not MembershipPlan.query.get(data["plan_id"]):
                return jsonify({"error": "plan_id no válido"}), 400
            m.plan_id = data["plan_id"]
        if "fecha_inicio" in data:
            m.fecha_inicio = parse_iso_date(data["fecha_inicio"])
        if "fecha_fin" in data:
            m.fecha_fin = parse_iso_date(data["fecha_fin"])
        if "estado" in data:
            m.estado = data["estado"]
        if "clases_usadas" in data:
            m.clases_usadas = data["clases_usadas"]
        db.session.commit()
        return jsonify(m.to_dict())

    @app.route("/memberships/<int:membership_id>", methods=["DELETE"])
    def delete_membership(membership_id):
        m = Membership.query.get_or_404(membership_id)
        db.session.delete(m)
        db.session.commit()
        return jsonify({"message": "Membership eliminado"})

    # ---------- CRUD CLASS TEMPLATES ----------

    @app.route("/class-templates", methods=["GET"])
    def list_class_templates():
        records = ClassTemplate.query.all()
        return jsonify([ct.to_dict() for ct in records])

    @app.route("/class-templates/<int:template_id>", methods=["GET"])
    def get_class_template(template_id):
        ct = ClassTemplate.query.get_or_404(template_id)
        return jsonify(ct.to_dict())

    @app.route("/class-templates", methods=["POST"])
    def create_class_template():
        data = request.get_json() or {}
        try:
            nombre = data["nombre"]
            coach_id = data["coach_id"]
            dia_semana = data["dia_semana"]
            hora_inicio = parse_time(data["hora_inicio"])
            hora_fin = parse_time(data["hora_fin"])
            capacidad = data["capacidad"]
            estado = data["estado"]
        except KeyError as e:
            return jsonify({"error": f"falta campo requerido {e.args[0]}"}), 400

        if not Coach.query.get(coach_id):
            return jsonify({"error": "coach_id no válido"}), 400

        ct = ClassTemplate(
            nombre=nombre,
            coach_id=coach_id,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            capacidad=capacidad,
            estado=estado,
            fecha_inicio=parse_iso_date(data.get("fecha_inicio")),
            fecha_fin=parse_iso_date(data.get("fecha_fin")),
        )
        db.session.add(ct)
        db.session.commit()
        return jsonify({"id": ct.id}), 201

    @app.route("/class-templates/<int:template_id>", methods=["PUT", "PATCH"])
    def update_class_template(template_id):
        ct = ClassTemplate.query.get_or_404(template_id)
        data = request.get_json() or {}
        if "nombre" in data:
            ct.nombre = data["nombre"]
        if "coach_id" in data:
            if not Coach.query.get(data["coach_id"]):
                return jsonify({"error": "coach_id no válido"}), 400
            ct.coach_id = data["coach_id"]
        if "dia_semana" in data:
            ct.dia_semana = data["dia_semana"]
        if "hora_inicio" in data:
            ct.hora_inicio = parse_time(data["hora_inicio"])
        if "hora_fin" in data:
            ct.hora_fin = parse_time(data["hora_fin"])
        if "capacidad" in data:
            ct.capacidad = data["capacidad"]
        if "estado" in data:
            ct.estado = data["estado"]
        if "fecha_inicio" in data:
            ct.fecha_inicio = parse_iso_date(data["fecha_inicio"])
        if "fecha_fin" in data:
            ct.fecha_fin = parse_iso_date(data["fecha_fin"])
        db.session.commit()
        return jsonify(ct.to_dict())

    @app.route("/class-templates/<int:template_id>", methods=["DELETE"])
    def delete_class_template(template_id):
        ct = ClassTemplate.query.get_or_404(template_id)
        db.session.delete(ct)
        db.session.commit()
        return jsonify({"message": "ClassTemplate eliminado"})

    # ---------- CRUD CLASS SESSIONS ----------

    @app.route("/class-sessions", methods=["GET"])
    def list_class_sessions():
        records = ClassSession.query.all()
        return jsonify([cs.to_dict() for cs in records])

    @app.route("/class-sessions/<int:session_id>", methods=["GET"])
    def get_class_session(session_id):
        cs = ClassSession.query.get_or_404(session_id)
        return jsonify(cs.to_dict())

    @app.route("/class-sessions", methods=["POST"])
    def create_class_session():
        data = request.get_json() or {}
        try:
            fecha = parse_iso_date(data["fecha"])
            hora_inicio = parse_time(data["hora_inicio"])
            hora_fin = parse_time(data["hora_fin"])
            coach_id = data["coach_id"]
            capacidad = data["capacidad"]
        except KeyError as e:
            return jsonify({"error": f"falta campo requerido {e.args[0]}"}), 400

        template_id = data.get("template_id")
        if template_id and not ClassTemplate.query.get(template_id):
            return jsonify({"error": "template_id no válido"}), 400
        if not Coach.query.get(coach_id):
            return jsonify({"error": "coach_id no válido"}), 400

        cs = ClassSession(
            template_id=template_id,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            coach_id=coach_id,
            capacidad=capacidad,
            estado=data.get("estado", "Programada"),
            nota=data.get("nota"),
        )
        db.session.add(cs)
        db.session.commit()
        return jsonify({"id": cs.id}), 201

    @app.route("/class-sessions/<int:session_id>", methods=["PUT", "PATCH"])
    def update_class_session(session_id):
        cs = ClassSession.query.get_or_404(session_id)
        data = request.get_json() or {}
        if "template_id" in data:
            if data["template_id"] is not None and not ClassTemplate.query.get(data["template_id"]):
                return jsonify({"error": "template_id no válido"}), 400
            cs.template_id = data["template_id"]
        if "fecha" in data:
            cs.fecha = parse_iso_date(data["fecha"])
        if "hora_inicio" in data:
            cs.hora_inicio = parse_time(data["hora_inicio"])
        if "hora_fin" in data:
            cs.hora_fin = parse_time(data["hora_fin"])
        if "coach_id" in data:
            if not Coach.query.get(data["coach_id"]):
                return jsonify({"error": "coach_id no válido"}), 400
            cs.coach_id = data["coach_id"]
        if "capacidad" in data:
            cs.capacidad = data["capacidad"]
        if "estado" in data:
            cs.estado = data["estado"]
        if "nota" in data:
            cs.nota = data["nota"]
        db.session.commit()
        return jsonify(cs.to_dict())

    @app.route("/class-sessions/<int:session_id>", methods=["DELETE"])
    def delete_class_session(session_id):
        cs = ClassSession.query.get_or_404(session_id)
        db.session.delete(cs)
        db.session.commit()
        return jsonify({"message": "ClassSession eliminado"})

    # ---------- CRUD BOOKINGS ----------

    @app.route("/bookings", methods=["GET"])
    def list_bookings():
        records = Booking.query.all()
        return jsonify([b.to_dict() for b in records])

    @app.route("/bookings/<int:booking_id>", methods=["GET"])
    def get_booking(booking_id):
        b = Booking.query.get_or_404(booking_id)
        return jsonify(b.to_dict())

    @app.route("/bookings", methods=["POST"])
    def create_booking():
        data = request.get_json() or {}
        try:
            session_id = data["session_id"]
            client_id = data["client_id"]
            estado = data["estado"]
        except KeyError as e:
            return jsonify({"error": f"falta campo requerido {e.args[0]}"}), 400

        session_obj = ClassSession.query.get(session_id)
        if not session_obj:
            return jsonify({"error": "session_id no válido"}), 400
        client = Client.query.get(client_id)
        if not client:
            return jsonify({"error": "client_id no válido"}), 400
        # Bloqueo si el cliente tiene saldo pendiente (>0)
        if float(client.saldo or 0) > 0:
            return jsonify({"error": "cliente tiene saldo pendiente, no puede reservar"}), 400
        membership_id = data.get("membership_id")
        membership = None
        if membership_id:
            membership = Membership.query.get(membership_id)
            if not membership:
                return jsonify({"error": "membership_id no válido"}), 400
            # Desactiva automáticamente si la fecha_fin ya pasó
            if membership.fecha_fin and membership.fecha_fin < date.today():
                membership.estado = "Inactiva"
                db.session.add(membership)
                db.session.commit()  # persist the state change even if we reject the booking
            if membership.estado != "Activa":
                return jsonify({"error": "la membresía no está activa"}), 400

            plan = membership.plan
            session_date = session_obj.fecha
            # No permitir reservas en fechas posteriores al vencimiento de la membresía
            if membership.fecha_fin and session_date and session_date > membership.fecha_fin:
                return jsonify({
                    "error": f"la membresía vence el {membership.fecha_fin.isoformat()} y la clase es el {session_date.isoformat()}"
                }), 400

            # Validación límite semanal
            if plan and plan.max_clases_por_semana is not None:
                # Semana calendario: lunes (0) a sábado (5) de la fecha de la sesión
                start_week = session_date - timedelta(days=session_date.weekday())
                end_week = start_week + timedelta(days=5)
                weekly_count = (
                    Booking.query.join(ClassSession, Booking.session_id == ClassSession.id)
                    .filter(
                        Booking.membership_id == membership.id,
                        Booking.estado == "Reservada",
                        ClassSession.fecha >= start_week,
                        ClassSession.fecha <= end_week,
                    )
                    .count()
                )
                if weekly_count >= plan.max_clases_por_semana:
                    return jsonify({"error": "límite semanal de la membresía alcanzado"}), 400

            # Validación límite total
            if plan and plan.max_clases_totales is not None:
                total_count = Booking.query.filter(
                    Booking.membership_id == membership.id,
                    Booking.estado == "Reservada",
                ).count()
                if total_count >= plan.max_clases_totales:
                    return jsonify({"error": "límite total de la membresía alcanzado"}), 400

        b = Booking(
            session_id=session_id,
            client_id=client_id,
            membership_id=membership_id,
            estado=estado,
            asistio=bool(data.get("asistio", False)),
            check_in_at=parse_iso_datetime(data.get("check_in_at")) if data.get("check_in_at") else None,
        )
        db.session.add(b)
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            return jsonify({"error": "No se pudo crear la reserva", "detail": str(exc)}), 400
        return jsonify({"id": b.id}), 201

    @app.route("/bookings/<int:booking_id>", methods=["PUT", "PATCH"])
    def update_booking(booking_id):
        b = Booking.query.get_or_404(booking_id)
        data = request.get_json() or {}
        if "session_id" in data:
            if not ClassSession.query.get(data["session_id"]):
                return jsonify({"error": "session_id no válido"}), 400
            b.session_id = data["session_id"]
        if "client_id" in data:
            if not Client.query.get(data["client_id"]):
                return jsonify({"error": "client_id no válido"}), 400
            b.client_id = data["client_id"]
        if "membership_id" in data:
            if data["membership_id"] is not None and not Membership.query.get(data["membership_id"]):
                return jsonify({"error": "membership_id no válido"}), 400
            b.membership_id = data["membership_id"]
        if "estado" in data:
            b.estado = data["estado"]
        if "asistio" in data:
            b.asistio = bool(data["asistio"])
        if "check_in_at" in data:
            b.check_in_at = parse_iso_datetime(data["check_in_at"]) if data["check_in_at"] else None
        db.session.commit()
        return jsonify(b.to_dict())

    @app.route("/bookings/<int:booking_id>", methods=["DELETE"])
    def delete_booking(booking_id):
        b = Booking.query.get_or_404(booking_id)
        db.session.delete(b)
        db.session.commit()
        return jsonify({"message": "Booking eliminado"})

    # ---------- ACCOUNT MOVEMENTS (multas / pagos) ----------

    @app.route("/account-movements", methods=["GET"])
    def list_account_movements():
        records = AccountMovement.query.order_by(AccountMovement.creado_en.desc()).all()
        return jsonify([m.to_dict() for m in records])

    @app.route("/account-movements/<int:movement_id>", methods=["GET"])
    def get_account_movement(movement_id):
        m = AccountMovement.query.get_or_404(movement_id)
        return jsonify(m.to_dict())

    @app.route("/account-movements", methods=["POST"])
    def create_account_movement():
        data = request.get_json() or {}
        try:
            client_id = data["client_id"]
            amount = data["amount"]
            tipo = data["tipo"]  # fine | payment | adjustment
        except KeyError as e:
            return jsonify({"error": f"falta campo requerido {e.args[0]}"}), 400

        client = Client.query.get(client_id)
        if not client:
            return jsonify({"error": "client_id no válido"}), 400

        booking_id = data.get("booking_id")
        if booking_id and not Booking.query.get(booking_id):
            return jsonify({"error": "booking_id no válido"}), 400

        # Campos adicionales para pagos (sólo aplica si tipo == payment)
        payment_type = data.get("payment_type")  # membership | multa | otro
        payment_method = data.get("payment_method")
        payment_reference = data.get("payment_reference")
        payment_date_str = data.get("payment_date") or data.get("fecha_pago")
        payment_membership_id = data.get("membership_id")
        payment_membership = None
        if payment_membership_id:
            payment_membership = Membership.query.get(payment_membership_id)
            if not payment_membership:
                return jsonify({"error": "membership_id no válido"}), 400

        # Manejo con Decimal para evitar errores de suma Decimal/float en saldo
        raw_amount = Decimal(str(amount))
        if tipo == "fine":
            signed_amount = abs(raw_amount)
        elif tipo == "payment":
            signed_amount = -abs(raw_amount)
            if payment_type and payment_type not in {"membership", "multa", "otro"}:
                return jsonify({"error": "payment_type debe ser membership, multa u otro"}), 400
        elif tipo == "adjustment":
            signed_amount = raw_amount
        else:
            return jsonify({"error": "tipo debe ser fine, payment o adjustment"}), 400

        movement = AccountMovement(
            client_id=client_id,
            amount=signed_amount,
            tipo=tipo,
            booking_id=booking_id,
            nota=data.get("nota"),
        )
        if tipo == "payment":
            payment = Payment(
                movement=movement,
                membership_id=payment_membership.id if payment_membership else None,
                payment_type=payment_type,
                payment_method=payment_method,
                payment_reference=payment_reference,
                fecha_pago=parse_iso_datetime(payment_date_str) if payment_date_str else datetime.utcnow(),
            )
            db.session.add(payment)
        apply_movement_and_update_balance(client, movement)
        db.session.commit()
        return jsonify(movement.to_dict()), 201
    
    prefix = app.config.get("URL_PREFIX", "/marehpilates")
    if prefix:
        # Montar la app bajo un prefijo (por ejemplo /coproda)
        def _not_found(environ, start_response):
            return Response("Not Found", status=404)(environ, start_response)

        app.wsgi_app = DispatcherMiddleware(_not_found, {prefix: app.wsgi_app})


    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
