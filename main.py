from datetime import date, timedelta
from gimnasio.auth import SesionAdmin
from gimnasio.controlador import GimnasioController
from gimnasio.membresias import (
    MembresiaBuilder,
    EntrenadorPersonalDecorator,
    PlanNutricionalDecorator,
    AccesoSpaDecorator,
)
from gimnasio.tarifas import TarifaMensual, TarifaAnual, TarifaCorporativa


def pantalla_login() -> bool:
    sesion = SesionAdmin()
    intentos = 3
    print("=" * 60)
    print("   ACCESO ADMINISTRATIVO - SISTEMA DE GIMNASIO")
    print("=" * 60)
    while intentos > 0:
        usuario = input("Usuario Admin (admin): ").strip()
        password = input("Contraseña (1234): ").strip()
        if sesion.iniciar_sesion(usuario, password):
            print(f"\n[OK] Bienvenido, {sesion.usuario_actual}. Sesión iniciada correctamente.")
            return True
        intentos -= 1
        print(f"[ERROR] Credenciales incorrectas. Intentos restantes: {intentos}\n")
    return False


def menu_principal():
    if not pantalla_login():
        print("Acceso bloqueado por seguridad.")
        return

    sesion = SesionAdmin()
    gym = GimnasioController()

    while sesion.autenticado:
        print("\n" + "=" * 60)
        print(f"   PANEL DE GESTIÓN DE GIMNASIO | Admin: {sesion.usuario_actual}")
        print("=" * 60)
        print("1. Ver lista completa de socios y vencimiento de membresías")
        print("2. Registrar nuevo socio")
        print("3. Asignar / Renovar membresía y servicios extra (Builder + Strategy + Decorator)")
        print("4. Validar ingreso por torniquete (Patrón Proxy)")
        print("5. Asignar rutina personalizada desde plantilla (Patrón Prototype)")
        print("6. Reservar / Deshacer clase grupal (Patrón Command)")
        print("0. Cerrar sesión y salir")

        opcion = input("\nSeleccione una opción: ").strip()

        try:
            if opcion == "1":
                print("\n--- LISTA DE SOCIOS REGISTRADOS ---")
                for socio in gym.socios.values():
                    print(" •", socio.resumen_estado())
                    if socio.rutina_asignada:
                        print(f"   └─ Rutina: {socio.rutina_asignada}")

            elif opcion == "2":
                id_s = input("ID Socio (ej. S03): ").strip().upper()
                nombre = input("Nombre completo: ").strip()
                dni = input("DNI: ").strip()
                tel = input("Teléfono: ").strip()
                socio = gym.registrar_socio(id_s, nombre, dni, tel)
                print(f"[OK] Socio registrado: {socio.resumen_estado()}")

            elif opcion == "3":
                id_s = input("ID del socio (ej. S01): ").strip().upper()
                plan = input("Nombre del plan (Básico / Gold / Black): ").strip()
                precio = float(input("Precio base mensual (S/): "))
                meses = int(input("Duración en meses (1, 6, 12): "))

                print("Tarifa: [1] Mensual  [2] Anual (-20%)  [3] Corporativa (-30%)")
                t_op = input("Elija tarifa: ").strip()
                estrategia = (
                    TarifaAnual() if t_op == "2"
                    else TarifaCorporativa() if t_op == "3"
                    else TarifaMensual()
                )

                membresia = (
                    MembresiaBuilder()
                    .set_plan(plan, precio)
                    .set_duracion(meses)
                    .agregar_zona("Musculación y Cardio")
                    .set_estrategia_tarifa(estrategia)
                    .build()
                )

                if input("¿Añadir Entrenador Personal (+S/120)? (s/n): ").lower() == "s":
                    membresia = EntrenadorPersonalDecorator(membresia)
                if input("¿Añadir Plan Nutricional (+S/80)? (s/n): ").lower() == "s":
                    membresia = PlanNutricionalDecorator(membresia)
                if input("¿Añadir Acceso Spa (+S/60)? (s/n): ").lower() == "s":
                    membresia = AccesoSpaDecorator(membresia)

                gym.asignar_membresia(id_s, membresia)
                print(f"\n[OK] Membresía asignada: {membresia.obtener_descripcion()}")
                print(f"Total cobrado: S/ {membresia.obtener_costo()}")

            elif opcion == "4":
                id_s = input("ID del socio que intenta ingresar (ej. S01 o S02): ").strip().upper()
                simular = input("¿Simular fecha futura para probar vencimiento? (s/n): ").lower()
                fecha_sim = None
                if simular == "s":
                    dias = int(input("¿Cuántos días en el futuro simular? (ej. 400): "))
                    fecha_sim = date.today() + timedelta(days=dias)
                _, mensaje = gym.verificar_ingreso(id_s, fecha_sim)
                print(mensaje)

            elif opcion == "5":
                id_s = input("ID del socio: ").strip().upper()
                plantilla = input("Plantilla base (hipertrofia / cardio): ").strip()
                extra = input("Ejercicio extra personalizado (Enter para omitir): ").strip() or None
                rutina = gym.asignar_rutina_clonada(id_s, plantilla, extra)
                print(f"[OK] Rutina asignada: {rutina}")

            elif opcion == "6":
                sub = input("[1] Reservar clase (spinning / yoga)  [2] Deshacer última reserva: ").strip()
                if sub == "1":
                    id_s = input("ID del socio: ").strip().upper()
                    clase = input("Clase (spinning / yoga): ").strip()
                    print(gym.reservar_clase(id_s, clase))
                elif sub == "2":
                    print(gym.deshacer_ultima_reserva())

            elif opcion == "0":
                sesion.cerrar_sesion()
                print("Sesión de administrador cerrada. ¡Hasta pronto!")
                break
            else:
                print("Opción inválida.")
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    menu_principal()