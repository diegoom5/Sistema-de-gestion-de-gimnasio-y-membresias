from abc import ABC, abstractmethod
import copy

#Patron prototype para clonar rutinas de entrenamiento del gimnasio.
class IPrototype(ABC):
    @abstractmethod
    def clonar(self):
        pass

#rutinas de entremamiento del gimnasio, se pueden clonar para asignarlas a diferentes socios.
class RutinaEntrenamiento(IPrototype):
    def __init__(self, nombre: str, objetivo: str, nivel: str, ejercicios: list[str] = None):
        self.nombre = nombre
        self.objetivo = objetivo
        self.nivel = nivel
        self.ejercicios = ejercicios if ejercicios is not None else []

    def agregar_ejercicio(self, ejercicio: str):
        self.ejercicios.append(ejercicio)

    def clonar(self) -> "RutinaEntrenamiento":
        return copy.deepcopy(self)

    def __str__(self) -> str:
        return f"{self.nombre} ({self.objetivo} - {self.nivel}): {', '.join(self.ejercicios)}"