from datetime import date
import sqlite3
from gimnasio.membresias import (
    AccesoSpaDecorator,
    EntrenadorPersonalDecorator,
    IMembresia,
    MembresiaBuilder,
    PlanNutricionalDecorator,
)
from gimnasio.rutinas import RutinaEntrenamiento
from gimnasio.socio import Socio
from gimnasio.tarifas import TarifaAnual, TarifaCorporativa, TarifaMensual


class ConexionBD:
   

    _instancia = None

    def __new__(cls, nombre_bd: str = "gimnasio.db"):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.nombre_bd = nombre_bd
            cls._instancia.conn = sqlite3.connect(nombre_bd)
            cls._instancia.conn.row_factory = sqlite3.Row
            cls._instancia._crear_tablas()
        return cls._instancia

    def _crear_tablas(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS socios (
                id_socio TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                dni TEXT NOT NULL,
                telefono TEXT,
                fecha_registro TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS membresias (
                id_socio TEXT PRIMARY KEY,
                plan_nombre TEXT NOT NULL,
                precio_base_mensual REAL NOT NULL,
                duracion_meses INTEGER NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_vencimiento TEXT NOT NULL,
                estrategia TEXT NOT NULL,
                extras TEXT NOT NULL,
                FOREIGN KEY (id_socio) REFERENCES socios (id_socio)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rutinas (
                id_socio TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                objetivo TEXT NOT NULL,
                nivel TEXT NOT NULL,
                ejercicios TEXT NOT NULL,
                FOREIGN KEY (id_socio) REFERENCES socios (id_socio)
            )
            """
        )
        self.conn.commit()


class RepositorioGimnasio:
    """Encapsula el acceso a SQLite para no mezclar SQL con la lógica de negocio."""

    def __init__(self, nombre_bd: str = "gimnasio.db"):
        self.db = ConexionBD(nombre_bd)
        self.conn = self.db.conn

    def guardar_socio(self, socio: Socio):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO socios (id_socio, nombre, dni, telefono, fecha_registro)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                socio.id_socio,
                socio.nombre,
                socio.dni,
                socio.telefono,
                socio.fecha_registro.isoformat(),
            ),
        )
        self.conn.commit()

    def guardar_membresia(self, id_socio: str, membresia: IMembresia):
        extras = []
        actual = membresia
        while hasattr(actual, "_membresia"):
            if isinstance(actual, EntrenadorPersonalDecorator):
                extras.append("entrenador")
            elif isinstance(actual, PlanNutricionalDecorator):
                extras.append("nutricion")
            elif isinstance(actual, AccesoSpaDecorator):
                extras.append("spa")
            actual = actual._membresia

        extras.reverse()
        estrategia_nombre = actual.estrategia_tarifa.__class__.__name__

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO membresias (
                id_socio, plan_nombre, precio_base_mensual, duracion_meses,
                fecha_inicio, fecha_vencimiento, estrategia, extras
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id_socio,
                actual.plan_nombre,
                actual.precio_base_mensual,
                actual.duracion_meses,
                actual.fecha_inicio.isoformat(),
                actual.fecha_vencimiento.isoformat(),
                estrategia_nombre,
                ",".join(extras),
            ),
        )
        self.conn.commit()

    def guardar_rutina(self, id_socio: str, rutina: RutinaEntrenamiento):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO rutinas (id_socio, nombre, objetivo, nivel, ejercicios)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                id_socio,
                rutina.nombre,
                rutina.objetivo,
                rutina.nivel,
                "|".join(rutina.ejercicios),
            ),
        )
        self.conn.commit()

    def cargar_socios(self) -> dict[str, Socio]:
        cursor = self.conn.cursor()
        filas_socios = cursor.execute("SELECT * FROM socios").fetchall()
        socios: dict[str, Socio] = {}

        for fila in filas_socios:
            socio = Socio(
                id_socio=fila["id_socio"],
                nombre=fila["nombre"],
                dni=fila["dni"],
                telefono=fila["telefono"] or "",
            )
            socio.fecha_registro = date.fromisoformat(fila["fecha_registro"])

            fila_mem = cursor.execute(
                "SELECT * FROM membresias WHERE id_socio = ?", (socio.id_socio,)
            ).fetchone()
            if fila_mem:
                estrategia = (
                    TarifaAnual()
                    if fila_mem["estrategia"] == "TarifaAnual"
                    else TarifaCorporativa()
                    if fila_mem["estrategia"] == "TarifaCorporativa"
                    else TarifaMensual()
                )
                fecha_ini = date.fromisoformat(fila_mem["fecha_inicio"])
                membresia: IMembresia = (
                    MembresiaBuilder()
                    .set_plan(fila_mem["plan_nombre"], fila_mem["precio_base_mensual"])
                    .set_duracion(fila_mem["duracion_meses"], fecha_inicio=fecha_ini)
                    .agregar_zona("Musculación y Cardio")
                    .set_estrategia_tarifa(estrategia)
                    .build()
                )
                membresia.fecha_vencimiento = date.fromisoformat(fila_mem["fecha_vencimiento"])

                if fila_mem["extras"]:
                    for extra in fila_mem["extras"].split(","):
                        if extra == "entrenador":
                            membresia = EntrenadorPersonalDecorator(membresia)
                        elif extra == "nutricion":
                            membresia = PlanNutricionalDecorator(membresia)
                        elif extra == "spa":
                            membresia = AccesoSpaDecorator(membresia)

                socio.membresia = membresia

            fila_rut = cursor.execute(
                "SELECT * FROM rutinas WHERE id_socio = ?", (socio.id_socio,)
            ).fetchone()
            if fila_rut:
                ejercicios = fila_rut["ejercicios"].split("|") if fila_rut["ejercicios"] else []
                socio.rutina_asignada = RutinaEntrenamiento(
                    nombre=fila_rut["nombre"],
                    objetivo=fila_rut["objetivo"],
                    nivel=fila_rut["nivel"],
                    ejercicios=ejercicios,
                )

            socios[socio.id_socio] = socio

        return socios