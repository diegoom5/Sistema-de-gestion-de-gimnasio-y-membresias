from datetime import date, timedelta
from gimnasio.acceso import ControlAccesoProxy, TorniqueteReal
from gimnasio.clases import ClaseGrupal, ICommand, ReservarClaseCommand
from gimnasio.membresias import (
    EntrenadorPersonalDecorator,
    IMembresia,
    MembresiaBuilder,
)
from gimnasio.rutinas import RutinaEntrenamiento
from gimnasio.socio import Socio
from gimnasio.tarifas import TarifaAnual, TarifaMensual


class GimnasioController:
    def __init__(self):
        self.socios: dict[str, Socio] = {}
        self.plantillas_rutinas: dict[str, RutinaEntrenamiento] = {
            "hipertrofia": RutinaEntrenamiento(
                "Hipertrofia Base",
                "Ganancia Muscular",
                "Intermedio",
                ["Press Banca 4x10", "Sentadilla Libre 4x8", "Remo con Barra 4x10"],
            ),
            "cardio": RutinaEntrenamiento(
                "Quema Grasa HIIT",
                "Pérdida de Peso",
                "Principiante",
                ["Burpees 3x15", "Salto de Cuerda 4x1min", "Mountain Climbers 3x20"],
            ),
        }
        self.clases_grupales: dict[str, ClaseGrupal] = {
            "spinning": ClaseGrupal("Spinning Extremo", "18:00 - 19:00", capacidad_max=2),
            "yoga": ClaseGrupal("Yoga Flow", "08:00 - 09:00", capacidad_max=10),
        }
        self.historial_comandos: list[ICommand] = []
        self.control_acceso = ControlAccesoProxy(TorniqueteReal("Puerta Principal"))
        self._cargar_datos_demo()

    def _cargar_datos_demo(self):
        s1 = Socio("S01", "Valeria Ríos", "71234567", "987654321")
        m1 = (
            MembresiaBuilder()
            .set_plan("Black VIP", 150.0)
            .set_duracion(12)
            .agregar_zona("Musculación")
            .agregar_zona("Piscina")
            .set_estrategia_tarifa(TarifaAnual())
            .build()
        )
        s1.membresia = EntrenadorPersonalDecorator(m1)
        self.socios[s1.id_socio] = s1

        s2 = Socio("S02", "Mateo Silva", "76543210", "912345678")
        inicio_vencido = date.today() - timedelta(days=35)
        s2.membresia = (
            MembresiaBuilder()
            .set_plan("Básico", 100.0)
            .set_duracion(1, fecha_inicio=inicio_vencido)
            .set_estrategia_tarifa(TarifaMensual())
            .build()
        )
        self.socios[s2.id_socio] = s2

    def registrar_socio(self, id_socio: str, nombre: str, dni: str, telefono: str = "") -> Socio:
        if id_socio in self.socios:
            raise ValueError(f"Ya existe un socio con el ID {id_socio}.")
        socio = Socio(id_socio, nombre, dni, telefono)
        self.socios[id_socio] = socio
        return socio

    def asignar_membresia(self, id_socio: str, membresia: IMembresia):
        socio = self._obtener_socio(id_socio)
        socio.membresia = membresia

    def asignar_rutina_clonada(
        self, id_socio: str, clave_plantilla: str, extra: str = None
    ) -> RutinaEntrenamiento:
        socio = self._obtener_socio(id_socio)
        plantilla = self.plantillas_rutinas.get(clave_plantilla.lower())
        if not plantilla:
            raise ValueError("Plantilla de rutina no encontrada.")
        clon = plantilla.clonar()
        if extra:
            clon.agregar_ejercicio(extra)
        socio.rutina_asignada = clon
        return clon

    def verificar_ingreso(
        self, id_socio: str, fecha_simulacion: date = None
    ) -> tuple[bool, str]:
        socio = self._obtener_socio(id_socio)
        return self.control_acceso.solicitar_ingreso(socio, fecha_simulacion)

    def reservar_clase(self, id_socio: str, clave_clase: str) -> str:
        socio = self._obtener_socio(id_socio)
        clase = self.clases_grupales.get(clave_clase.lower())
        if not clase:
            raise ValueError("Clase grupal no encontrada.")
        cmd = ReservarClaseCommand(clase, socio)
        self.historial_comandos.append(cmd)
        return cmd.ejecutar()

    def deshacer_ultima_reserva(self) -> str:
        if not self.historial_comandos:
            return "No hay reservas recientes para deshacer."
        return self.historial_comandos.pop().deshacer()

    def _obtener_socio(self, id_socio: str) -> Socio:
        socio = self.socios.get(id_socio)
        if not socio:
            raise ValueError(f"No se encontró al socio {id_socio}.")
        return socio