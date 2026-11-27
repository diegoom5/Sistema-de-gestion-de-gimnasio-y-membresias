from datetime import date


class Socio:
    def __init__(self, id_socio: str, nombre: str, dni: str, telefono: str = ""):
        self.id_socio = id_socio
        self.nombre = nombre
        self.dni = dni
        self.telefono = telefono
        self.fecha_registro = date.today()
        self.membresia = None
        self.rutina_asignada = None

    def resumen_estado(self) -> str:
        if not self.membresia:
            return f"[{self.id_socio}] {self.nombre} (DNI: {self.dni}) | Sin membresía asignada"
        estado = "ACTIVA" if self.membresia.esta_vigente() else "VENCIDA"
        return (
            f"[{self.id_socio}] {self.nombre} | Plan: {self.membresia.obtener_plan()} | "
            f"Estado: {estado} | Vence: {self.membresia.obtener_fecha_vencimiento()} "
            f"({self.membresia.dias_restantes()} días restantes) | "
            f"Costo: S/{self.membresia.obtener_costo()}"
        )