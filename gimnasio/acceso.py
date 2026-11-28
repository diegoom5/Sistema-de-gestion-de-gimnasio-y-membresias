from abc import ABC, abstractmethod
from datetime import date
from gimnasio.socio import Socio
#Patron proxy para controlar el acceso de los socios al gimnasio mediante un torniquete.

class IControlAcceso(ABC):
    @abstractmethod
    def solicitar_ingreso(self, socio: Socio, fecha_actual: date = None) -> tuple[bool, str]:
        pass


class TorniqueteReal(IControlAcceso):
    def __init__(self, ubicacion: str = "Entrada Principal"):
        self.ubicacion = ubicacion

    def solicitar_ingreso(self, socio: Socio, fecha_actual: date = None) -> tuple[bool, str]:
        dias = socio.membresia.dias_restantes(fecha_actual)
        msg = f"[TORNIQUETE {self.ubicacion}] Acceso PERMITIDO a {socio.nombre}. Le quedan {dias} días de membresía."
        return True, msg


class ControlAccesoProxy(IControlAcceso):
    def __init__(self, torniquete_real: TorniqueteReal):
        self._torniquete_real = torniquete_real
        self.historial_accesos: list[str] = []

    def solicitar_ingreso(self, socio: Socio, fecha_actual: date = None) -> tuple[bool, str]:
        if socio.membresia is None:
            msg = f"[ACCESO DENEGADO] {socio.nombre} no cuenta con una membresía."
            self.historial_accesos.append(msg)
            return False, msg

        if not socio.membresia.esta_vigente(fecha_actual):
            vence = socio.membresia.obtener_fecha_vencimiento()
            msg = f"[ACCESO DENEGADO] La membresía de {socio.nombre} venció el {vence}."
            self.historial_accesos.append(msg)
            return False, msg

        permitido, msg = self._torniquete_real.solicitar_ingreso(socio, fecha_actual)
        self.historial_accesos.append(msg)
        return permitido, msg