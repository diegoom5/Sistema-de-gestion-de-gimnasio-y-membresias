from abc import ABC, abstractmethod
from gimnasio.socio import Socio

#Patron command para manejar la reserva de clases grupales del gimnasio.
class ClaseGrupal:
    def __init__(self, nombre: str, horario: str, capacidad_max: int):
        self.nombre = nombre
        self.horario = horario
        self.capacidad_max = capacidad_max
        self.inscritos: list[Socio] = []
        self.lista_espera: list[Socio] = []

    def inscribir(self, socio: Socio) -> str:
        if socio in self.inscritos or socio in self.lista_espera:
            return f"{socio.nombre} ya está registrado en {self.nombre}."
        if len(self.inscritos) < self.capacidad_max:
            self.inscritos.append(socio)
            return f"Reserva CONFIRMADA para {socio.nombre} en {self.nombre} ({self.horario})."
        self.lista_espera.append(socio)
        return f"Cupos llenos en {self.nombre}. {socio.nombre} pasó a LISTA DE ESPERA (#{len(self.lista_espera)})."

    def cancelar_inscripcion(self, socio: Socio) -> str:
        if socio in self.inscritos:
            self.inscritos.remove(socio)
            msg = f"Reserva CANCELADA para {socio.nombre} en {self.nombre}."
            if self.lista_espera:
                promovido = self.lista_espera.pop(0)
                self.inscritos.append(promovido)
                msg += f" -> {promovido.nombre} fue promovido automáticamente desde la lista de espera."
            return msg
        if socio in self.lista_espera:
            self.lista_espera.remove(socio)
            return f"{socio.nombre} salió de la lista de espera de {self.nombre}."
        return f"{socio.nombre} no tenía reserva en {self.nombre}."


class ICommand(ABC):
    @abstractmethod
    def ejecutar(self) -> str:
        pass

    @abstractmethod
    def deshacer(self) -> str:
        pass


class ReservarClaseCommand(ICommand):
    def __init__(self, clase: ClaseGrupal, socio: Socio):
        self.clase = clase
        self.socio = socio

    def ejecutar(self) -> str:
        return self.clase.inscribir(self.socio)

    def deshacer(self) -> str:
        return self.clase.cancelar_inscripcion(self.socio)