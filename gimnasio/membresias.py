from abc import ABC, abstractmethod
from datetime import date, timedelta
from gimnasio.tarifas import IEstrategiaTarifa, TarifaMensual

#patron builder para construir membresias del gimnasio y patron decorator para agregar servicios adicionales a las membresias.

class IMembresia(ABC):
    @abstractmethod
    def obtener_plan(self) -> str:
        pass

    @abstractmethod
    def obtener_costo(self) -> float:
        pass

    @abstractmethod
    def obtener_descripcion(self) -> str:
        pass

    @abstractmethod
    def esta_vigente(self, fecha_consulta: date = None) -> bool:
        pass

    @abstractmethod
    def obtener_fecha_vencimiento(self) -> date:
        pass

    @abstractmethod
    def dias_restantes(self, fecha_consulta: date = None) -> int:
        pass


class MembresiaBase(IMembresia):
    def __init__(self):
        self.plan_nombre: str = "Básico"
        self.precio_base_mensual: float = 100.0
        self.duracion_meses: int = 1
        self.fecha_inicio: date = date.today()
        self.fecha_vencimiento: date = date.today() + timedelta(days=30)
        self.zonas: list[str] = []
        self.dias_congelamiento: int = 0
        self.invitados_mes: int = 0
        self.suspendida: bool = False
        self.estrategia_tarifa: IEstrategiaTarifa = TarifaMensual()

    def obtener_plan(self) -> str:
        return self.plan_nombre

    def obtener_costo(self) -> float:
        return self.estrategia_tarifa.calcular_precio(
            self.precio_base_mensual, self.duracion_meses
        )

    def obtener_descripcion(self) -> str:
        zonas_str = ", ".join(self.zonas) if self.zonas else "Zona General"
        return (
            f"Plan {self.plan_nombre} ({self.duracion_meses} mes/es) | "
            f"Inicio: {self.fecha_inicio} -> Vence: {self.fecha_vencimiento} | "
            f"Zonas: [{zonas_str}] | {self.estrategia_tarifa.obtener_nombre()}"
        )

    def esta_vigente(self, fecha_consulta: date = None) -> bool:
        if self.suspendida:
            return False
        hoy = fecha_consulta or date.today()
        return hoy <= self.fecha_vencimiento

    def obtener_fecha_vencimiento(self) -> date:
        return self.fecha_vencimiento

    def dias_restantes(self, fecha_consulta: date = None) -> int:
        hoy = fecha_consulta or date.today()
        return max(0, (self.fecha_vencimiento - hoy).days)


class MembresiaBuilder:
    def __init__(self):
        self._membresia = MembresiaBase()

    def set_plan(self, nombre: str, precio_base_mensual: float) -> "MembresiaBuilder":
        self._membresia.plan_nombre = nombre
        self._membresia.precio_base_mensual = precio_base_mensual
        return self

    def set_duracion(self, meses: int, fecha_inicio: date = None) -> "MembresiaBuilder":
        if meses <= 0:
            raise ValueError("La duración debe ser mayor a 0 meses.")
        inicio = fecha_inicio or date.today()
        self._membresia.duracion_meses = meses
        self._membresia.fecha_inicio = inicio
        self._membresia.fecha_vencimiento = inicio + timedelta(days=30 * meses)
        return self

    def agregar_zona(self, zona: str) -> "MembresiaBuilder":
        self._membresia.zonas.append(zona)
        return self

    def set_congelamiento(self, dias: int) -> "MembresiaBuilder":
        self._membresia.dias_congelamiento = dias
        return self

    def set_invitados(self, cantidad: int) -> "MembresiaBuilder":
        self._membresia.invitados_mes = cantidad
        return self

    def set_estrategia_tarifa(self, estrategia: IEstrategiaTarifa) -> "MembresiaBuilder":
        self._membresia.estrategia_tarifa = estrategia
        return self

    def build(self) -> MembresiaBase:
        resultado = self._membresia
        self._membresia = MembresiaBase()
        return resultado


class ServicioAdicionalDecorator(IMembresia, ABC):
    def __init__(self, membresia_envuelta: IMembresia):
        self._membresia = membresia_envuelta

    def obtener_plan(self) -> str:
        return self._membresia.obtener_plan()

    def obtener_costo(self) -> float:
        return self._membresia.obtener_costo()

    def obtener_descripcion(self) -> str:
        return self._membresia.obtener_descripcion()

    def esta_vigente(self, fecha_consulta: date = None) -> bool:
        return self._membresia.esta_vigente(fecha_consulta)

    def obtener_fecha_vencimiento(self) -> date:
        return self._membresia.obtener_fecha_vencimiento()

    def dias_restantes(self, fecha_consulta: date = None) -> int:
        return self._membresia.dias_restantes(fecha_consulta)


class EntrenadorPersonalDecorator(ServicioAdicionalDecorator):
    COSTO_EXTRA = 120.0

    def obtener_costo(self) -> float:
        return round(self._membresia.obtener_costo() + self.COSTO_EXTRA, 2)

    def obtener_descripcion(self) -> str:
        return f"{self._membresia.obtener_descripcion()} + [Entrenador Personal +S/{self.COSTO_EXTRA}]"


class PlanNutricionalDecorator(ServicioAdicionalDecorator):
    COSTO_EXTRA = 80.0

    def obtener_costo(self) -> float:
        return round(self._membresia.obtener_costo() + self.COSTO_EXTRA, 2)

    def obtener_descripcion(self) -> str:
        return f"{self._membresia.obtener_descripcion()} + [Nutrición +S/{self.COSTO_EXTRA}]"


class AccesoSpaDecorator(ServicioAdicionalDecorator):
    COSTO_EXTRA = 60.0

    def obtener_costo(self) -> float:
        return round(self._membresia.obtener_costo() + self.COSTO_EXTRA, 2)

    def obtener_descripcion(self) -> str:
        return f"{self._membresia.obtener_descripcion()} + [Spa & Sauna +S/{self.COSTO_EXTRA}]"