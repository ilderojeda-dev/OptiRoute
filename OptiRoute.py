import random

def crear_matriz(n):
    return [[0 for _ in range(n)] for _ in range(n)]


def llenar_matriz_aleatoria(matriz, peso_min=1, peso_max=20, prob_extra=0.4):
    n = len(matriz)

    orden = list(range(n))

    # Mezcla aleatoriamente el orden de los nodos.
    random.shuffle(orden)

    # Este primer for crea un ciclo que pasa por todos los nodos
    for i in range(n):
        origen = orden[i]
        # El % n permite que, al llegar al último nodo, vuelva nuevamente al primero.
        destino = orden[(i + 1) % n]
        peso = random.randint(peso_min, peso_max)
        matriz[origen][destino] = peso
        matriz[destino][origen] = peso

    # algunas conexiones adicionales.
    for i in range(n):
        for j in range(i + 1, n):
            # random.random() genera un número entre 0 y 1.
            # Si es menor que prob_extra, se agrega la conexión.
            if matriz[i][j] == 0 and random.random() < prob_extra:
                peso = random.randint(peso_min, peso_max)
                matriz[i][j] = peso
                matriz[j][i] = peso

    return matriz

def llenar_matriz_manual(matriz):
    n = len(matriz)
    for i in range(n):
        # De esta forma no pedimos dos veces la misma conexión.
        for j in range(i + 1, n):
            peso = int(input(
                f"Peso nodo {i+1} - nodo {j+1}: "
            ))
            matriz[i][j] = peso
            matriz[j][i] = peso
    return matriz

def mostrar_matriz(matriz):
    print("\nMatriz de costos:")
    for fila in matriz:
        print(fila)


# FUERZA BRUTA MEDIANTE RECURSIVIDAD
def generar_rutas_FB(ruta, restantes, matriz, soluciones):

    # CASO BASE:
    # Si ya no quedan nodos por visitar,
    # intentamos regresar al nodo inicial.
    if len(restantes) == 0:

        inicio = ruta[0]
        ultimo = ruta[-1]

        # Solo existe un ciclo si el último nodo
        # tiene conexión con el nodo inicial.
        if matriz[ultimo][inicio] != 0:

            ruta_final = ruta + [inicio]
            costo = calcular_costo(ruta_final, matriz)

            # Evita guardar el mismo ciclo recorrido al revés.
            if ruta[1] < ruta[-1]:
                soluciones.append({
                    "ruta": ruta_final,
                    "costo": costo
                })

        return

    # Nodo donde estamos actualmente.
    actual = ruta[-1]

    # Probamos cada nodo que todavía falta visitar.
    for nodo in restantes:

        # Solo podemos avanzar si existe una arista.
        if matriz[actual][nodo] != 0:

            # Creamos una nueva lista sin el nodo elegido.
            nuevos_restantes = restantes.copy()
            nuevos_restantes.remove(nodo)

            # Continuamos la búsqueda desde ese nodo.
            generar_rutas_FB(
                ruta + [nodo],
                nuevos_restantes,
                matriz,
                soluciones
            )

def calcular_costo(ruta, matriz):
    costo = 0

    for i in range(len(ruta)-1):
        origen = ruta[i]
        destino = ruta[i+1]

        if matriz[origen][destino] == 0:
            return None

        costo += matriz[origen][destino]

    return costo


# MERGE SORT
def merge_sort(lista):
    if len(lista) <= 1:
        return lista

    mitad = len(lista)//2

    izquierda = merge_sort(lista[:mitad])
    derecha = merge_sort(lista[mitad:])

    return merge(izquierda, derecha)


def merge(izquierda, derecha):
    resultado = []

    i = 0
    j = 0

    while i < len(izquierda) and j < len(derecha):

        if izquierda[i]["costo"] <= derecha[j]["costo"]:
            resultado.append(izquierda[i])
            i += 1
        else:
            resultado.append(derecha[j])
            j += 1

    resultado.extend(izquierda[i:])
    resultado.extend(derecha[j:])

    return resultado


def mostrar_mejores(soluciones):
    soluciones = merge_sort(soluciones)

    print("\n==============================")
    print("TOP 5 RUTAS MÁS ÓPTIMAS")
    print("==============================")

    cantidad = min(10, len(soluciones))

    for i in range(cantidad):
        ruta = soluciones[i]["ruta"]
        costo = soluciones[i]["costo"]

        ruta_texto = " -> ".join(
            str(nodo + 1) for nodo in ruta
        )

        print(f"\n{i+1}. Ruta: {ruta_texto}")
        print(f"   Costo: {costo}")


def main():
    print("==============================")
    print("        OPTIROUTE")
    print("Problema del Agente Viajero")
    print("==============================")

    n = int(input("\nCantidad de nodos [5-10]: "))

    matriz = crear_matriz(n)

    print("\n1. Generar aleatorio")
    print("2. Ingresar manual")

    opcion = int(input("Seleccione opción: "))

    if opcion == 1:
        matriz = llenar_matriz_aleatoria(matriz)
    else:
        matriz = llenar_matriz_manual(matriz)

    mostrar_matriz(matriz)

    soluciones = []

    print("\nCalculando rutas mediante fuerza bruta...")

    generar_rutas_FB(
        [0],
        list(range(1, n)),
        matriz,
        soluciones
    )

    print("\nCantidad de rutas evaluadas:", len(soluciones))

    if len(soluciones) > 0:
        mostrar_mejores(soluciones)

        mejor = merge_sort(soluciones)[0]

        print("\n==============================")
        print("RUTA ÓPTIMA")
        print("==============================")

        print(
            "Ruta:",
            " -> ".join(
                str(n+1) for n in mejor["ruta"]
            )
        )

        print("Costo mínimo:", mejor["costo"])

    else:
        print("\nNo existen ciclos hamiltonianos.")


if __name__ == "__main__":
    main()