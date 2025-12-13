from flask import Flask, jsonify, request
from config import Config
from models import db, Producto, Cliente, Orden, OrdenItem, Usuario, CategoriaProducto, MarcaProducto, Tienda, Talla
from flask_migrate import Migrate
from datetime import datetime
from flask_cors import CORS
from datetime import datetime



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

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
