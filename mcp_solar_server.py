import csv
import json
from pathlib import Path
from datetime import date
from typing import Optional

from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).parent
PRODUCTS_FILE = BASE_DIR / "solar_productos.csv"
LEADS_FILE = BASE_DIR / "solar_leads.csv"
INSTALLATIONS_FILE = BASE_DIR / "solar_instalaciones.csv"
APPOINTMENTS_FILE = BASE_DIR / "solar_citas.csv"

mcp = FastMCP("MCP Solar Empresarial")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def append_csv(path: Path, row: dict, fieldnames: list[str]) -> None:
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not exists or path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(row)


@mcp.tool()
def buscar_productos(
    texto: str = "",
    categoria: Optional[str] = None,
    potencia_min_w: Optional[int] = None,
    solo_disponibles: bool = True,
) -> list[dict]:
    """Busca productos solares en el catálogo de ejemplo."""
    texto = texto.lower().strip()
    results = []
    for product in read_csv(PRODUCTS_FILE):
        haystack = f"{product.get('nombre', '')} {product.get('marca', '')} {product.get('sku', '')}".lower()
        if texto and texto not in haystack:
            continue
        if categoria and product.get("categoria", "").lower() != categoria.lower():
            continue
        if potencia_min_w is not None and int(product.get("potencia_w") or 0) < potencia_min_w:
            continue
        if solo_disponibles and int(product.get("stock") or 0) <= 0:
            continue
        results.append(product)
    return results


@mcp.tool()
def consultar_stock(sku: str) -> dict:
    """Devuelve stock y disponibilidad de un SKU."""
    for product in read_csv(PRODUCTS_FILE):
        if product.get("sku", "").lower() == sku.lower():
            stock = int(product.get("stock") or 0)
            return {"sku": sku, "stock": stock, "disponible": stock > 0}
    return {"sku": sku, "stock": 0, "disponible": False, "encontrado": False}


@mcp.tool()
def calcular_ahorro(
    potencia_instalada_kw: float,
    consumo_mensual_kwh: float,
    tarifa_eur_kwh: float = 0.20,
    horas_solares_equivalentes: float = 4.5,
    factor_rendimiento: float = 0.80,
) -> dict:
    """Calcula una estimación orientativa de producción, ahorro y retorno."""
    produccion_anual_kwh = potencia_instalada_kw * horas_solares_equivalentes * 365 * factor_rendimiento
    consumo_anual_kwh = consumo_mensual_kwh * 12
    energia_autoconsumida = min(produccion_anual_kwh, consumo_anual_kwh)
    ahorro_anual = energia_autoconsumida * tarifa_eur_kwh
    return {
        "produccion_anual_kwh": round(produccion_anual_kwh, 2),
        "consumo_anual_kwh": round(consumo_anual_kwh, 2),
        "energia_autoconsumida_kwh": round(energia_autoconsumida, 2),
        "ahorro_anual_eur": round(ahorro_anual, 2),
        "ahorro_mensual_promedio_eur": round(ahorro_anual / 12, 2),
        "supuestos": {
            "tarifa_eur_kwh": tarifa_eur_kwh,
            "horas_solares_equivalentes": horas_solares_equivalentes,
            "factor_rendimiento": factor_rendimiento,
        },
        "nota": "Estimación inicial. Validar con ubicación, orientación, sombras y tarifa real.",
    }


@mcp.tool()
def calcular_presupuesto(
    consumo_mensual_kwh: float,
    potencia_objetivo_kw: float,
    incluye_bateria: bool = False,
    tarifa_eur_kwh: float = 0.20,
) -> dict:
    """Genera un presupuesto de ejemplo usando el catálogo CSV."""
    paneles_necesarios = max(1, round((potencia_objetivo_kw * 1000) / 450))
    panel = next((p for p in read_csv(PRODUCTS_FILE) if p["sku"] == "PAN-450-MONO"), None)
    inversor = next((p for p in read_csv(PRODUCTS_FILE) if p["sku"] == "INV-5K-HIB"), None)
    estructura = next((p for p in read_csv(PRODUCTS_FILE) if p["sku"] == "EST-01"), None)
    bateria = next((p for p in read_csv(PRODUCTS_FILE) if p["sku"] == "BAT-10K"), None)

    items = []

    def add_item(product: Optional[dict], quantity: int) -> None:
        if not product:
            return
        items.append({
            "sku": product["sku"],
            "nombre": product["nombre"],
            "cantidad": quantity,
            "precio_unitario": float(product["precio_unitario"]),
            "subtotal": round(quantity * float(product["precio_unitario"]), 2),
        })

    add_item(panel, paneles_necesarios)
    add_item(inversor, 1)
    add_item(estructura, 1)
    if incluye_bateria:
        add_item(bateria, 1)

    subtotal = round(sum(item["subtotal"] for item in items), 2)
    instalacion = round(max(900, potencia_objetivo_kw * 220), 2)
    subtotal_con_instalacion = subtotal + instalacion
    impuestos = round(subtotal_con_instalacion * 0.21, 2)
    total = round(subtotal_con_instalacion + impuestos, 2)
    ahorro = calcular_ahorro(potencia_objetivo_kw, consumo_mensual_kwh, tarifa_eur_kwh)

    return {
        "items": items,
        "instalacion_eur": instalacion,
        "subtotal_eur": subtotal_con_instalacion,
        "impuestos_eur": impuestos,
        "total_eur": total,
        "ahorro": ahorro,
        "retorno_aproximado_anios": round(total / ahorro["ahorro_anual_eur"], 1) if ahorro["ahorro_anual_eur"] else None,
        "nota": "Presupuesto de ejemplo, sujeto a visita técnica y validación comercial.",
    }


@mcp.tool()
def registrar_lead(
    nombre: str,
    email: str,
    telefono: str,
    ciudad: str,
    consumo_mensual_kwh: float,
    interes: str,
    origen: str = "web",
) -> dict:
    """Registra un cliente potencial en el CSV de ejemplo."""
    existing = read_csv(LEADS_FILE)
    next_number = 1001 + len(existing)
    lead_id = f"L-{next_number}"
    row = {
        "lead_id": lead_id,
        "nombre": nombre,
        "email": email,
        "telefono": telefono,
        "ciudad": ciudad,
        "consumo_mensual_kwh": str(consumo_mensual_kwh),
        "interes": interes,
        "estado": "nuevo",
        "origen": origen,
    }
    append_csv(LEADS_FILE, row, list(row.keys()))
    return row


@mcp.tool()
def consultar_instalacion(
    cliente: str = "",
    ciudad: str = "",
    estado: str = "",
) -> list[dict]:
    """Consulta instalaciones por cliente, ciudad o estado."""
    results = []
    for item in read_csv(INSTALLATIONS_FILE):
        if cliente and cliente.lower() not in item.get("cliente", "").lower():
            continue
        if ciudad and ciudad.lower() != item.get("ciudad", "").lower():
            continue
        if estado and estado.lower() != item.get("estado", "").lower():
            continue
        results.append(item)
    return results


@mcp.tool()
def crear_cita(
    lead_id: str,
    cliente: str,
    fecha: str,
    hora: str,
    tipo: str = "visita_tecnica",
    tecnico: str = "Por asignar",
) -> dict:
    """Crea una cita en el CSV de ejemplo."""
    existing = read_csv(APPOINTMENTS_FILE)
    next_number = 3001 + len(existing)
    row = {
        "cita_id": f"C-{next_number}",
        "lead_id": lead_id,
        "cliente": cliente,
        "fecha": fecha,
        "hora": hora,
        "tipo": tipo,
        "tecnico": tecnico,
        "estado": "pendiente_confirmacion",
        "notas": "",
    }
    append_csv(APPOINTMENTS_FILE, row, list(row.keys()))
    return row


@mcp.tool()
def consultar_citas(fecha: str = "", estado: str = "") -> list[dict]:
    """Consulta citas por fecha o estado."""
    return [
        item for item in read_csv(APPOINTMENTS_FILE)
        if (not fecha or item.get("fecha") == fecha)
        and (not estado or item.get("estado", "").lower() == estado.lower())
    ]


if __name__ == "__main__":
    mcp.run()