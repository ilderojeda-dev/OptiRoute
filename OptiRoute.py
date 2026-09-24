from itertools import permutations
import random


def pedir_numero_nodos():
    while True:
        try:
            n = int(input("Ingrese la cantidad de nodos [5 - 10]: "))

            if 5 <= n <= 10:
                return n

            print("Error: la cantidad de nodos debe estar entre 5 y 10.")

        except ValueError:
            print("Error: debe ingresar un número entero.")


def crear_matriz(n):
    return [[0 for _ in range(n)] for _ in range(n)]


def crear_grafo_manual(n):
    matriz = crear_matriz(n)

    print("\n--- GENERACIÓN MANUAL DEL GRAFO ---")
    print("Indique si existe una conexión entre cada par de nodos.\n")

    for i in range(n):
        for j in range(i + 1, n):

            while True:
                respuesta = input(
                    f"¿Existe conexión entre nodo {i + 1} y nodo {j + 1}? (s/n): "
                ).lower()

                if respuesta in ["s", "n"]:
                    break

                print("Ingrese solamente 's' o 'n'.")

            if respuesta == "s":

                while True:
                    try:
                        peso = float(input("Ingrese el peso de la arista: "))

                        if peso > 0:
                            break

                        print("El peso debe ser mayor que cero.")

                    except ValueError:
                        print("Ingrese un valor numérico.")

                matriz[i][j] = peso
                matriz[j][i] = peso

    return matriz


def crear_grafo_aleatorio(n):
    matriz = crear_matriz(n)

    # Primero se crea un ciclo para garantizar
    # que exista al menos un ciclo hamiltoniano.
    for i in range(n - 1):
        peso = random.randint(1, 20)

        matriz[i][i + 1] = peso
        matriz[i + 1][i] = peso

    peso = random.randint(1, 20)

    matriz[n - 1][0] = peso
    matriz[0][n - 1] = peso

    # Se agregan algunas conexiones adicionales.
    for i in range(n):
        for j in range(i + 1, n):

            if matriz[i][j] == 0 and random.random() < 0.40:
                peso = random.randint(1, 20)

                matriz[i][j] = peso
                matriz[j][i] = peso

    return matriz


def mostrar_matriz(matriz):
    print("\n--- MATRIZ DE COSTOS ---\n")

    print("      ", end="")

    for i in range(len(matriz)):
        print(f"{i + 1:^8}", end="")

    print()

    for i, fila in enumerate(matriz):
        print(f"{i + 1:^6}", end="")

        for valor in fila:
            print(f"{valor:^8g}", end="")

        print()


def calcular_costo(ruta, matriz):
    costo = 0

    for i in range(len(ruta) - 1):
        origen = ruta[i]
        destino = ruta[i + 1]

        if matriz[origen][destino] == 0:
            return None

        costo += matriz[origen][destino]

    return costo


def buscar_ciclos_hamiltonianos(matriz):
    n = len(matriz)

    nodo_inicial = 0
    otros_nodos = list(range(1, n))

    ciclos = []

    for permutacion in permutations(otros_nodos):

        # Evita contar dos veces el mismo ciclo
        # recorrido en sentidos contrarios.
        if permutacion[0] > permutacion[-1]:
            continue

        ruta = [nodo_inicial] + list(permutacion) + [nodo_inicial]

        costo = calcular_costo(ruta, matriz)

        if costo is not None:
            ciclos.append((ruta, costo))

    return ciclos


def buscar_aristas_faltantes(matriz):
    n = len(matriz)

    nodo_inicial = 0
    otros_nodos = list(range(1, n))

    mejor_ruta = None
    menos_aristas_faltantes = None

    for permutacion in permutations(otros_nodos):

        ruta = [nodo_inicial] + list(permutacion) + [nodo_inicial]

        faltantes = []

        for i in range(len(ruta) - 1):
            origen = ruta[i]
            destino = ruta[i + 1]

            if matriz[origen][destino] == 0:
                faltantes.append((origen, destino))

        if (
            menos_aristas_faltantes is None
            or len(faltantes) < len(menos_aristas_faltantes)
        ):
            mejor_ruta = ruta
            menos_aristas_faltantes = faltantes

    return mejor_ruta, menos_aristas_faltantes


def mostrar_ruta(ruta):
    return " -> ".join(str(nodo + 1) for nodo in ruta)


def mostrar_resultados(ciclos):
    if not ciclos:
        return

    print("\n--- CICLOS HAMILTONIANOS ENCONTRADOS ---\n")

    for numero, (ruta, costo) in enumerate(ciclos, start=1):
        print(
            f"Ciclo {numero}: {mostrar_ruta(ruta)} | "
            f"Costo total: {costo:g}"
        )

    ruta_optima, costo_optimo = min(ciclos, key=lambda ciclo: ciclo[1])

    print("\n--- SOLUCIÓN ÓPTIMA ---")
    print(f"Cantidad de ciclos encontrados: {len(ciclos)}")
    print(f"Ruta óptima: {mostrar_ruta(ruta_optima)}")
    print(f"Costo mínimo: {costo_optimo:g}")


def main():
    print("=" * 50)
    print("                    OptiRoute")
    print("          Problema del Agente Viajero")
    print("=" * 50)

    n = pedir_numero_nodos()

    print("\n¿Cómo desea generar el grafo?")
    print("1. Manual")
    print("2. Aleatorio")

    while True:
        opcion = input("\nSeleccione una opción: ")

        if opcion == "1":
            matriz = crear_grafo_manual(n)
            break

        elif opcion == "2":
            matriz = crear_grafo_aleatorio(n)
            break

        else:
            print("Seleccione una opción válida.")

    mostrar_matriz(matriz)

    print("\nBuscando ciclos hamiltonianos mediante fuerza bruta...")

    ciclos = buscar_ciclos_hamiltonianos(matriz)

    if ciclos:
        mostrar_resultados(ciclos)

    else:
        print("\nNo se encontró ningún ciclo hamiltoniano.")

        ruta, faltantes = buscar_aristas_faltantes(matriz)

        print("\nPara completar al menos un ciclo hamiltoniano podrían")
        print("incorporarse las siguientes aristas:")

        for origen, destino in faltantes:
            print(f"- Nodo {origen + 1} <-> Nodo {destino + 1}")

        print("\nUn posible ciclo sería:")
        print(mostrar_ruta(ruta))


if __name__ == "__main__":
    main()