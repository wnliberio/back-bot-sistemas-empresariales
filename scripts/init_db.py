# ============================================================================
# RUTA: backend/scripts/init_db.py
# DESCRIPCIÓN: Script para inicializar MongoDB con colecciones y datos
# USO: python scripts/init_db.py (ejecutar ANTES de main.py)
# ============================================================================

import os
import sys
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ Error: MONGO_URI no está configurado en .env")
    sys.exit(1)

print(f"📌 Conectando a MongoDB...")

try:
    # Conectar con ServerApi
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    client.admin.command('ping')
    print("✅ Pinged your deployment. You successfully connected to MongoDB!")
    
    db = client["fresst_chatbot"]
    
    # ===== 1. CREAR COLECCIÓN: cuentas_bancarias =====
    print("\n📝 Creando: cuentas_bancarias")
    
    if "cuentas_bancarias" not in db.list_collection_names():
        cuentas = db["cuentas_bancarias"]
        cuenta_pichincha = {
            "banco": "Pichincha",
            "titular": "FRESST",
            "numero_cuenta": "3152965478",
            "tipo_cuenta": "Corriente",
            "activo": True,
            "fecha_creacion": datetime.now()
        }
        cuentas.insert_one(cuenta_pichincha)
        print("   ✅ 1 cuenta creada")
    else:
        print("   ⚠️  Ya existe")
    
    # ===== 2. CREAR COLECCIÓN: productos =====
    print("\n📝 Creando: productos")
    
    if "productos" not in db.list_collection_names():
        productos = db["productos"]
        
        productos_data = [
            # REFRIGERACIÓN
            {
                "nombre": "Frigoríficos",
                "categoria": "refrigeracion",
                "precio": 2500,
                "caracteristicas": "Capacidad 800L, Consumo 150W, Garantía 2 años",
                "descripcion": "Frigoríficos profesionales para negocios",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Vitrinas Horizontales",
                "categoria": "refrigeracion",
                "precio": 1800,
                "caracteristicas": "Cristal templado, Iluminación LED",
                "descripcion": "Vitrinas refrigeradas horizontales",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Vitrinas Verticales",
                "categoria": "refrigeracion",
                "precio": 2100,
                "caracteristicas": "Puerta de cristal, Luz interior",
                "descripcion": "Vitrinas refrigeradas verticales",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Bomboneras",
                "categoria": "refrigeracion",
                "precio": 1500,
                "caracteristicas": "Diseño elegante, Temperatura controlada",
                "descripcion": "Bomboneras refrigeradas",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            
            # COCCIÓN
            {
                "nombre": "Hornos",
                "categoria": "coccion",
                "precio": 3500,
                "caracteristicas": "Industrial, Gas/Eléctrico, Capacidad 50kg",
                "descripcion": "Hornos profesionales",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Freidoras",
                "categoria": "coccion",
                "precio": 2200,
                "caracteristicas": "Capacidad 30L, Termostato regulable",
                "descripcion": "Freidoras profesionales",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Cocinas",
                "categoria": "coccion",
                "precio": 2800,
                "caracteristicas": "4 quemadores, Encendido electrónico",
                "descripcion": "Cocinas profesionales",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Asaderos",
                "categoria": "coccion",
                "precio": 4000,
                "caracteristicas": "A carbón, Acero inoxidable",
                "descripcion": "Asaderos profesionales",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            
            # MOBILIARIO
            {
                "nombre": "Mesas de Acero",
                "categoria": "mobiliario",
                "precio": 800,
                "caracteristicas": "Acero inoxidable 430",
                "descripcion": "Mesas de acero para cocinas",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Estanterías",
                "categoria": "mobiliario",
                "precio": 500,
                "caracteristicas": "Acero, Ajustable, Capacidad 100kg",
                "descripcion": "Estanterías industriales",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Góndolas",
                "categoria": "mobiliario",
                "precio": 1500,
                "caracteristicas": "Metálicas, Varios estantes",
                "descripcion": "Góndolas para exhibición",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            
            # ESPECIALES
            {
                "nombre": "Carros de Hotdogs",
                "categoria": "especiales",
                "precio": 2000,
                "caracteristicas": "Tapa de vidrio, Ruedas giratorias",
                "descripcion": "Carros para vender hotdogs",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Balanza",
                "categoria": "especiales",
                "precio": 300,
                "caracteristicas": "Mecánica, Capacidad 50kg",
                "descripcion": "Balanza comercial",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Balanza Digital",
                "categoria": "especiales",
                "precio": 600,
                "caracteristicas": "Digital, Precisión 1g",
                "descripcion": "Balanza digital de precisión",
                "activo": True,
                "fecha_creacion": datetime.now()
            },
        ]
        
        result = productos.insert_many(productos_data)
        print(f"   ✅ {len(result.inserted_ids)} productos creados")
    else:
        print("   ⚠️  Ya existe")
    
    # ===== 3. CREAR COLECCIONES VACÍAS =====
    print("\n📝 Creando colecciones vacías:")
    
    for coleccion in ["leads", "ordenes", "conversaciones_whatsapp"]:
        if coleccion not in db.list_collection_names():
            db.create_collection(coleccion)
            print(f"   ✅ {coleccion}")
        else:
            print(f"   ⚠️  {coleccion} ya existe")
    
    # ===== 4. CREAR ÍNDICES =====
    print("\n📝 Creando índices:")
    
    db["leads"].create_index("telefono")
    print("   ✅ leads.telefono")
    
    db["ordenes"].create_index("id_lead")
    db["ordenes"].create_index("estado")
    print("   ✅ ordenes (id_lead, estado)")
    
    db["conversaciones_whatsapp"].create_index("id_lead")
    print("   ✅ conversaciones_whatsapp.id_lead")
    
    # ===== RESUMEN =====
    print("\n" + "="*60)
    print("✅ BASE DE DATOS INICIALIZADA CORRECTAMENTE")
    print("="*60)
    
    collections = db.list_collection_names()
    print(f"\n📊 Colecciones: {len(collections)}")
    for col in collections:
        count = db[col].count_documents({})
        print(f"   - {col}: {count} documentos")
    
    print("\n✨ MongoDB está listo para usar!")
    print("   Ejecuta: python main.py")
    
    client.close()

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nVerifica:")
    print("   1. MONGO_URI sea correcto en .env")
    print("   2. Tu IP esté en Network Access (MongoDB Atlas)")
    print("   3. La contraseña sea válida")
    sys.exit(1)