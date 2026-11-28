from abc import ABC, abstractmethod

#Patron stragegy para calcular el precio de las tarifas del gimnasio.
class IEstrategiaTarifa(ABC):
    @abstractmethod
    def calcular_precio(self, precio_base_mensual: float, meses: int) -> float:
        pass

    @abstractmethod
    def obtener_nombre(self) -> str:
        pass


class TarifaMensual(IEstrategiaTarifa):
    def calcular_precio(self, precio_base_mensual: float, meses: int) -> float:
        return round(precio_base_mensual * meses, 2)

    def obtener_nombre(self) -> str:
        return "Tarifa Regular (0% desc.)"


class TarifaAnual(IEstrategiaTarifa):
    def calcular_precio(self, precio_base_mensual: float, meses: int) -> float:
        return round((precio_base_mensual * meses) * 0.80, 2)

    def obtener_nombre(self) -> str:
        return "Tarifa Anual (20% desc.)"


class TarifaCorporativa(IEstrategiaTarifa):
    def calcular_precio(self, precio_base_mensual: float, meses: int) -> float:
        return round((precio_base_mensual * meses) * 0.70, 2)

    def obtener_nombre(self) -> str:
        return "Tarifa Corporativa (30% desc.)"