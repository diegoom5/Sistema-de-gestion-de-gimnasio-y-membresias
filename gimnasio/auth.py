class SesionAdmin:
    _instancia = None
# Se utilizó patrón sigleton para garantizar la sesión de administrador en el sistema
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(SesionAdmin, cls).__new__(cls)
            cls._instancia.autenticado = False
            cls._instancia.usuario_actual = None
            # Credenciales de administradores del gimnasio
            cls._instancia._credenciales = {
                "diegoom5": "Promocion2017", #Gerente
                "recepcion": "recepcion123", #Personal de administración
            }
        return cls._instancia

    def iniciar_sesion(self, usuario: str, password: str) -> bool:
        if self._credenciales.get(usuario) == password:
            self.autenticado = True
            self.usuario_actual = usuario
            return True
        return False

    def cerrar_sesion(self):
        self.autenticado = False
        self.usuario_actual = None