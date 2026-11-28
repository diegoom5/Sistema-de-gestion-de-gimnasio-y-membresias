from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox, ttk

from gimnasio.acceso import ControlAccesoProxy, TorniqueteReal
from gimnasio.auth import SesionAdmin
from gimnasio.clases import ClaseGrupal, ICommand, ReservarClaseCommand
from gimnasio.membresias import (
    AccesoSpaDecorator,
    EntrenadorPersonalDecorator,
    IMembresia,
    MembresiaBuilder,
    PlanNutricionalDecorator,
)
from gimnasio.rutinas import RutinaEntrenamiento
from gimnasio.socio import Socio
from gimnasio.tarifas import (
    IEstrategiaTarifa,
    TarifaAnual,
    TarifaCorporativa,
    TarifaMensual,
)


class ControladorGUI:
    """Controlador del sistema conectado a la interfaz gráfica."""

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
        id_socio = id_socio.strip()
        nombre = nombre.strip()
        dni = dni.strip()
        telefono = telefono.strip()
        if not id_socio or not nombre or not dni:
            raise ValueError("ID, nombre y DNI son obligatorios.")
        if id_socio in self.socios:
            raise ValueError(f"Ya existe un socio con el ID '{id_socio}'.")
        socio = Socio(id_socio, nombre, dni, telefono)
        self.socios[id_socio] = socio
        return socio

    def asignar_membresia(
        self,
        id_socio: str,
        plan_nombre: str,
        precio_base: float,
        meses: int,
        estrategia: IEstrategiaTarifa,
        entrenador: bool,
        nutricion: bool,
        spa: bool,
    ) -> IMembresia:
        socio = self._obtener_socio(id_socio)
        builder = (
            MembresiaBuilder()
            .set_plan(plan_nombre, precio_base)
            .set_duracion(meses)
            .agregar_zona("Musculación")
            .agregar_zona("Cardio")
            .set_estrategia_tarifa(estrategia)
        )
        if plan_nombre.upper().find("VIP") != -1 or plan_nombre.upper().find("BLACK") != -1:
            builder.agregar_zona("Piscina").set_invitados(2).set_congelamiento(15)

        membresia: IMembresia = builder.build()
        if entrenador:
            membresia = EntrenadorPersonalDecorator(membresia)
        if nutricion:
            membresia = PlanNutricionalDecorator(membresia)
        if spa:
            membresia = AccesoSpaDecorator(membresia)

        socio.membresia = membresia
        return membresia

    def asignar_rutina_clonada(
        self, id_socio: str, clave_plantilla: str, extra: str | None = None
    ) -> RutinaEntrenamiento:
        socio = self._obtener_socio(id_socio)
        plantilla = self.plantillas_rutinas.get(clave_plantilla.lower())
        if not plantilla:
            raise ValueError("Plantilla de rutina no encontrada.")
        clon = plantilla.clonar()
        if extra and extra.strip():
            clon.agregar_ejercicio(extra.strip())
        socio.rutina_asignada = clon
        return clon

    def verificar_ingreso(
        self, id_socio: str, fecha_simulacion: date | None = None
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
        socio = self.socios.get(id_socio.strip())
        if not socio:
            raise ValueError(f"No se encontró al socio con ID '{id_socio}'.")
        return socio


class AplicacionGimnasioGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión de Gimnasio y Membresías")
        self.geometry("920x600")
        self.minsize(820, 520)

        self.sesion = SesionAdmin()
        self.controlador = ControladorGUI()
        self.intentos_restantes = 3

        self._configurar_estilos()
        self.contenedor = tk.Frame(self)
        self.contenedor.pack(fill="both", expand=True)

        self.mostrar_login()

    def _configurar_estilos(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=[12, 6], font=("Segoe UI", 10, "bold"))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)

    def _limpiar_contenedor(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    def mostrar_login(self):
        self._limpiar_contenedor()
        self.intentos_restantes = 3

        marco_externo = tk.Frame(self.contenedor, bg="#1e242b")
        marco_externo.pack(fill="both", expand=True)

        tarjeta = tk.Frame(marco_externo, bg="#ffffff", padx=35, pady=30, relief="raised", bd=1)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            tarjeta,
            text="Gimnasio & Membresías",
            font=("Segoe UI", 18, "bold"),
            bg="#ffffff",
            fg="#1e242b",
        ).pack(pady=(0, 4))

        tk.Label(
            tarjeta,
            text="Inicia sesión como administrador",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#555555",
        ).pack(pady=(0, 20))

        tk.Label(tarjeta, text="Usuario", font=("Segoe UI", 10, "bold"), bg="#ffffff", anchor="w").pack(
            fill="x"
        )
        entry_usuario = tk.Entry(tarjeta, font=("Segoe UI", 11), width=28)
        entry_usuario.pack(pady=(4, 12), ipady=4)
        entry_usuario.focus_set()

        tk.Label(
            tarjeta, text="Contraseña", font=("Segoe UI", 10, "bold"), bg="#ffffff", anchor="w"
        ).pack(fill="x")
        entry_pass = tk.Entry(tarjeta, font=("Segoe UI", 11), width=28, show="*")
        entry_pass.pack(pady=(4, 18), ipady=4)

        lbl_estado = tk.Label(tarjeta, text="", font=("Segoe UI", 9), bg="#ffffff", fg="#b00020")
        lbl_estado.pack(pady=(0, 8))

        def intentar_login(event=None):
            usuario = entry_usuario.get().strip()
            password = entry_pass.get()
            if self.sesion.iniciar_sesion(usuario, password):
                self.mostrar_panel_principal()
            else:
                self.intentos_restantes -= 1
                if self.intentos_restantes <= 0:
                    messagebox.showerror(
                        "Acceso bloqueado",
                        "Se agotaron los intentos permitidos. El programa se cerrará.",
                    )
                    self.destroy()
                else:
                    lbl_estado.config(
                        text=f"Credenciales incorrectas. Intentos restantes: {self.intentos_restantes}"
                    )
                    entry_pass.delete(0, tk.END)

        entry_pass.bind("<Return>", intentar_login)

        tk.Button(
            tarjeta,
            text="Iniciar sesión",
            font=("Segoe UI", 10, "bold"),
            bg="#0d6efd",
            fg="#ffffff",
            activebackground="#0b5ed7",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=intentar_login,
        ).pack(fill="x")

    def mostrar_panel_principal(self):
        self._limpiar_contenedor()

        barra_superior = tk.Frame(self.contenedor, bg="#1e242b", padx=16, pady=10)
        barra_superior.pack(fill="x")

        tk.Label(
            barra_superior,
            text=f"Panel de Gestión  |  Admin: {self.sesion.usuario_actual}",
            font=("Segoe UI", 12, "bold"),
            bg="#1e242b",
            fg="#ffffff",
        ).pack(side="left")

        tk.Button(
            barra_superior,
            text="Cerrar sesión",
            font=("Segoe UI", 9, "bold"),
            bg="#dc3545",
            fg="#ffffff",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._cerrar_sesion,
        ).pack(side="right")

        notebook = ttk.Notebook(self.contenedor)
        notebook.pack(fill="both", expand=True, padx=12, pady=10)

        tab_socios = tk.Frame(notebook, padx=14, pady=12)
        tab_membresias = tk.Frame(notebook, padx=14, pady=12)
        tab_acceso = tk.Frame(notebook, padx=14, pady=12)
        tab_rutinas_clases = tk.Frame(notebook, padx=14, pady=12)

        notebook.add(tab_socios, text="Socios y Registro")
        notebook.add(tab_membresias, text="Membresías y Extras")
        notebook.add(tab_acceso, text="Torniquete ")
        notebook.add(tab_rutinas_clases, text="Rutinas y Clases")

        self._construir_tab_socios(tab_socios)
        self._construir_tab_membresias(tab_membresias)
        self._construir_tab_acceso(tab_acceso)
        self._construir_tab_rutinas_clases(tab_rutinas_clases)
        self.refrescar_tabla_socios()

    def _cerrar_sesion(self):
        self.sesion.cerrar_sesion()
        self.mostrar_login()

    def _construir_tab_socios(self, parent):
        # Formulario registro de socio
        frame_form = tk.LabelFrame(
            parent, text="Registrar nuevo socio", font=("Segoe UI", 10, "bold"), padx=12, pady=10
        )
        frame_form.pack(fill="x", pady=(0, 12))

        tk.Label(frame_form, text="ID:", font=("Segoe UI", 9)).grid(row=0, column=0, padx=4, sticky="e")
        e_id = tk.Entry(frame_form, width=10)
        e_id.grid(row=0, column=1, padx=(0, 10))

        tk.Label(frame_form, text="Nombre:", font=("Segoe UI", 9)).grid(
            row=0, column=2, padx=4, sticky="e"
        )
        e_nombre = tk.Entry(frame_form, width=22)
        e_nombre.grid(row=0, column=3, padx=(0, 10))

        tk.Label(frame_form, text="DNI:", font=("Segoe UI", 9)).grid(row=0, column=4, padx=4, sticky="e")
        e_dni = tk.Entry(frame_form, width=14)
        e_dni.grid(row=0, column=5, padx=(0, 10))

        tk.Label(frame_form, text="Teléfono:", font=("Segoe UI", 9)).grid(
            row=0, column=6, padx=4, sticky="e"
        )
        e_tel = tk.Entry(frame_form, width=14)
        e_tel.grid(row=0, column=7, padx=(0, 10))

        def guardar_socio():
            try:
                socio = self.controlador.registrar_socio(
                    e_id.get(), e_nombre.get(), e_dni.get(), e_tel.get()
                )
                e_id.delete(0, tk.END)
                e_nombre.delete(0, tk.END)
                e_dni.delete(0, tk.END)
                e_tel.delete(0, tk.END)
                self.refrescar_tabla_socios()
                messagebox.showinfo("Socio registrado", f"Socio '{socio.nombre}' ({socio.id_socio}) guardado.")
            except ValueError as err:
                messagebox.showerror("Error", str(err))

        tk.Button(
            frame_form,
            text="Registrar",
            font=("Segoe UI", 9, "bold"),
            bg="#198754",
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=guardar_socio,
        ).grid(row=0, column=8, padx=4)

        # Tabla de socios
        frame_tabla = tk.LabelFrame(
            parent,
            text="Lista de socios y estado de membresía",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10,
        )
        frame_tabla.pack(fill="both", expand=True)

        columnas = ("id", "nombre", "dni", "plan", "vence", "dias", "estado", "rutina")
        self.tabla_socios = ttk.Treeview(frame_tabla, columns=columnas, show="headings")

        encabezados = {
            "id": ("ID", 70),
            "nombre": ("Nombre", 150),
            "dni": ("DNI", 95),
            "plan": ("Plan", 120),
            "vence": ("Vencimiento", 105),
            "dias": ("Días rest.", 85),
            "estado": ("Estado", 95),
            "rutina": ("Rutina asignada", 170),
        }
        for col, (texto, ancho) in encabezados.items():
            self.tabla_socios.heading(col, text=texto)
            self.tabla_socios.column(col, width=ancho, anchor="center" if col != "nombre" else "w")

        scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_socios.yview)
        self.tabla_socios.configure(yscrollcommand=scroll.set)

        self.tabla_socios.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        tk.Button(
            parent,
            text="Actualizar lista",
            font=("Segoe UI", 9),
            command=self.refrescar_tabla_socios,
        ).pack(anchor="e", pady=(6, 0))

    def refrescar_tabla_socios(self):
        if not hasattr(self, "tabla_socios"):
            return
        for item in self.tabla_socios.get_children():
            self.tabla_socios.delete(item)

        hoy = date.today()
        for socio in self.controlador.socios.values():
            if socio.membresia:
                plan = socio.membresia.obtener_plan()
                vence = socio.membresia.obtener_fecha_vencimiento().isoformat()
                dias = str(socio.membresia.dias_restantes(hoy))
                estado = "Vigente" if socio.membresia.esta_vigente(hoy) else "Vencida"
            else:
                plan = "Sin plan"
                vence = "-"
                dias = "0"
                estado = "Sin membresía"

            rutina = socio.rutina_asignada.nombre if socio.rutina_asignada else "Sin rutina"
            self.tabla_socios.insert(
                "", "end", values=(socio.id_socio, socio.nombre, socio.dni, plan, vence, dias, estado, rutina)
            )

    def _construir_tab_membresias(self, parent):
        form = tk.LabelFrame(
            parent,
            text="Configurar y asignar membresía ",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=14,
        )
        form.pack(fill="both", expand=True)

        tk.Label(form, text="ID del socio:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", pady=6
        )
        e_id = tk.Entry(form, width=18, font=("Segoe UI", 10))
        e_id.grid(row=0, column=1, sticky="w", pady=6)

        tk.Label(form, text="Plan:", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=6)
        combo_plan = ttk.Combobox(
            form,
            values=["Básico (S/100)", "Fit Plus (S/130)", "Black VIP (S/150)"],
            state="readonly",
            width=22,
        )
        combo_plan.current(0)
        combo_plan.grid(row=1, column=1, sticky="w", pady=6)

        tk.Label(form, text="Duración (meses):", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky="w", pady=6
        )
        spin_meses = tk.Spinbox(form, from_=1, to=24, width=8, font=("Segoe UI", 10))
        spin_meses.grid(row=2, column=1, sticky="w", pady=6)

        tk.Label(form, text="Tarifa (Strategy):", font=("Segoe UI", 10)).grid(
            row=3, column=0, sticky="w", pady=6
        )
        combo_tarifa = ttk.Combobox(
            form,
            values=["Mensual", "Anual (-20%)", "Corporativa (-15%)"],
            state="readonly",
            width=22,
        )
        combo_tarifa.current(0)
        combo_tarifa.grid(row=3, column=1, sticky="w", pady=6)

        var_entrenador = tk.BooleanVar()
        var_nutricion = tk.BooleanVar()
        var_spa = tk.BooleanVar()

        tk.Label(form, text="Extras (Decorator):", font=("Segoe UI", 10)).grid(
            row=4, column=0, sticky="nw", pady=6
        )
        frame_extras = tk.Frame(form)
        frame_extras.grid(row=4, column=1, sticky="w", pady=6)
        tk.Checkbutton(frame_extras, text="Entrenador Personal (+S/120)", variable=var_entrenador).pack(
            anchor="w"
        )
        tk.Checkbutton(frame_extras, text="Plan Nutricional (+S/80)", variable=var_nutricion).pack(
            anchor="w"
        )
        tk.Checkbutton(frame_extras, text="Acceso Spa & Sauna (+S/60)", variable=var_spa).pack(
            anchor="w"
        )

        txt_resultado = tk.Text(form, height=6, width=75, font=("Consolas", 9), state="disabled")
        txt_resultado.grid(row=6, column=0, columnspan=2, pady=12, sticky="nsew")

        def asignar():
            try:
                plan_sel = combo_plan.get()
                if "Black VIP" in plan_sel:
                    nombre_plan, precio_base = "Black VIP", 150.0
                elif "Fit Plus" in plan_sel:
                    nombre_plan, precio_base = "Fit Plus", 130.0
                else:
                    nombre_plan, precio_base = "Básico", 100.0

                meses = int(spin_meses.get())
                tarifa_sel = combo_tarifa.get()
                if "Anual" in tarifa_sel:
                    estrategia = TarifaAnual()
                elif "Corporativa" in tarifa_sel:
                    estrategia = TarifaCorporativa()
                else:
                    estrategia = TarifaMensual()

                mem = self.controlador.asignar_membresia(
                    e_id.get(),
                    nombre_plan,
                    precio_base,
                    meses,
                    estrategia,
                    var_entrenador.get(),
                    var_nutricion.get(),
                    var_spa.get(),
                )
                self.refrescar_tabla_socios()

                detalle = (
                    f"Membresía asignada correctamente.\n"
                    f"Costo total: S/ {mem.obtener_costo():.2f}\n"
                    f"Detalle: {mem.obtener_descripcion()}"
                )
                txt_resultado.config(state="normal")
                txt_resultado.delete("1.0", tk.END)
                txt_resultado.insert("1.0", detalle)
                txt_resultado.config(state="disabled")
            except Exception as err:
                messagebox.showerror("Error al asignar membresía", str(err))

        tk.Button(
            form,
            text="Asignar membresía",
            font=("Segoe UI", 10, "bold"),
            bg="#0d6efd",
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=asignar,
        ).grid(row=5, column=1, sticky="w", pady=6)

    def _construir_tab_acceso(self, parent):
        marco = tk.LabelFrame(
            parent,
            text="Validar ingreso en torniquete ",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=14,
        )
        marco.pack(fill="both", expand=True)

        tk.Label(marco, text="ID del socio:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", pady=6
        )
        e_id = tk.Entry(marco, width=18, font=("Segoe UI", 10))
        e_id.grid(row=0, column=1, sticky="w", pady=6)

        var_simular = tk.BooleanVar()
        tk.Checkbutton(
            marco, text="Simular fecha futura", variable=var_simular, font=("Segoe UI", 10)
        ).grid(row=1, column=0, sticky="w", pady=6)

        frame_dias = tk.Frame(marco)
        frame_dias.grid(row=1, column=1, sticky="w", pady=6)
        tk.Label(frame_dias, text="Días en el futuro:", font=("Segoe UI", 10)).pack(side="left")
        e_dias = tk.Entry(frame_dias, width=8, font=("Segoe UI", 10))
        e_dias.insert(0, "0")
        e_dias.pack(side="left", padx=6)

        lbl_respuesta = tk.Label(
            marco,
            text="Ingresa un ID de socio y presiona 'Validar ingreso'.",
            font=("Segoe UI", 11, "bold"),
            wraplength=680,
            justify="left",
            pady=16,
        )
        lbl_respuesta.grid(row=3, column=0, columnspan=2, sticky="w")

        def validar():
            try:
                fecha_sim = None
                if var_simular.get():
                    dias_futuro = int(e_dias.get().strip() or "0")
                    fecha_sim = date.today() + timedelta(days=dias_futuro)

                permitido, mensaje = self.controlador.verificar_ingreso(e_id.get(), fecha_sim)
                lbl_respuesta.config(
                    text=mensaje, fg="#198754" if permitido else "#dc3545"
                )
            except Exception as err:
                messagebox.showerror("Error", str(err))

        tk.Button(
            marco,
            text="Validar ingreso",
            font=("Segoe UI", 10, "bold"),
            bg="#0d6efd",
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=validar,
        ).grid(row=2, column=1, sticky="w", pady=8)

    def _construir_tab_rutinas_clases(self, parent):
        # Izquierda: Rutinas (Prototype)
        frame_rut = tk.LabelFrame(
            parent,
            text="Rutina personalizada ",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=12,
        )
        frame_rut.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(frame_rut, text="ID del socio:", font=("Segoe UI", 9)).pack(anchor="w")
        e_id_rut = tk.Entry(frame_rut, width=20, font=("Segoe UI", 10))
        e_id_rut.pack(anchor="w", pady=(2, 8))

        tk.Label(frame_rut, text="Plantilla base:", font=("Segoe UI", 9)).pack(anchor="w")
        combo_plantilla = ttk.Combobox(
            frame_rut, values=["hipertrofia", "cardio"], state="readonly", width=18
        )
        combo_plantilla.current(0)
        combo_plantilla.pack(anchor="w", pady=(2, 8))

        tk.Label(frame_rut, text="Ejercicio extra (opcional):", font=("Segoe UI", 9)).pack(anchor="w")
        e_extra = tk.Entry(frame_rut, width=28, font=("Segoe UI", 10))
        e_extra.pack(anchor="w", pady=(2, 10))

        lbl_rut_res = tk.Label(
            frame_rut, text="", font=("Segoe UI", 9), wraplength=340, justify="left", fg="#1e242b"
        )
        lbl_rut_res.pack(anchor="w", pady=6)

        def asignar_rutina():
            try:
                clon = self.controlador.asignar_rutina_clonada(
                    e_id_rut.get(), combo_plantilla.get(), e_extra.get()
                )
                self.refrescar_tabla_socios()
                lbl_rut_res.config(
                    text=f"Asignada '{clon.nombre}': {', '.join(clon.ejercicios)}", fg="#198754"
                )
            except Exception as err:
                messagebox.showerror("Error", str(err))

        tk.Button(
            frame_rut,
            text="Clonar y asignar rutina",
            font=("Segoe UI", 9, "bold"),
            bg="#0d6efd",
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=asignar_rutina,
        ).pack(anchor="w")

        # Derecha: Clases grupales (Command)
        frame_cls = tk.LabelFrame(
            parent,
            text="Clases grupales ",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=12,
        )
        frame_cls.pack(side="right", fill="both", expand=True, padx=(8, 0))

        tk.Label(frame_cls, text="ID del socio:", font=("Segoe UI", 9)).pack(anchor="w")
        e_id_cls = tk.Entry(frame_cls, width=20, font=("Segoe UI", 10))
        e_id_cls.pack(anchor="w", pady=(2, 8))

        tk.Label(frame_cls, text="Clase:", font=("Segoe UI", 9)).pack(anchor="w")
        combo_clase = ttk.Combobox(
            frame_cls, values=["spinning", "yoga"], state="readonly", width=18
        )
        combo_clase.current(0)
        combo_clase.pack(anchor="w", pady=(2, 10))

        lbl_cls_res = tk.Label(
            frame_cls, text="", font=("Segoe UI", 9), wraplength=340, justify="left"
        )
        lbl_cls_res.pack(anchor="w", pady=8)

        def reservar():
            try:
                msg = self.controlador.reservar_clase(e_id_cls.get(), combo_clase.get())
                lbl_cls_res.config(text=msg, fg="#198754")
            except Exception as err:
                messagebox.showerror("Error", str(err))

        def deshacer():
            msg = self.controlador.deshacer_ultima_reserva()
            lbl_cls_res.config(text=msg, fg="#0d6efd")

        frame_btns = tk.Frame(frame_cls)
        frame_btns.pack(anchor="w")

        tk.Button(
            frame_btns,
            text="Reservar clase",
            font=("Segoe UI", 9, "bold"),
            bg="#198754",
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=reservar,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            frame_btns,
            text="Deshacer última",
            font=("Segoe UI", 9, "bold"),
            bg="#6c757d",
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=deshacer,
        ).pack(side="left")


if __name__ == "__main__":
    app = AplicacionGimnasioGUI()
    app.mainloop()