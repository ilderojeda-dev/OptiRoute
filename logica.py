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
        # El % n permite que, al llegar al ultimo nodo, vuelva al primero.
        destino = orden[(i + 1) % n]
        peso = random.randint(peso_min, peso_max)
        matriz[origen][destino] = peso
        matriz[destino][origen] = peso

    # Algunas conexiones adicionales
    for i in range(n):
        for j in range(i + 1, n):
            # random.random() genera un numero entre 0 y 1.
            # Si es menor que prob_extra, se agrega la conexion.
            if matriz[i][j] == 0 and random.random() < prob_extra:
                peso = random.randint(peso_min, peso_max)
                matriz[i][j] = peso
                matriz[j][i] = peso

    return matriz


def agregar_arista(matriz, origen, destino, peso):
    matriz[origen][destino] = peso
    matriz[destino][origen] = peso


def borrar_aristas(matriz):
    n = len(matriz)
    for i in range(n):
        for j in range(n):
            matriz[i][j] = 0

# VALIDACION: ¿EL GRAFO PERMITE FORMAR UN CICLO HAMILTONIANO?

def intentar_cerrar_ciclo(matriz, ruta, restantes):
    if len(restantes) == 0:
        inicio = ruta[0]
        ultimo = ruta[-1]
        return matriz[ultimo][inicio] != 0

    actual = ruta[-1]
    for nodo in restantes:
        if matriz[actual][nodo] != 0:
            nuevos_restantes = restantes.copy()
            nuevos_restantes.remove(nodo)
            if intentar_cerrar_ciclo(matriz, ruta + [nodo], nuevos_restantes):
                return True

    return False


def existe_ciclo_hamiltoniano(matriz):
    n = len(matriz)
    return intentar_cerrar_ciclo(matriz, [0], list(range(1, n)))


def generar_candidatos_ciclo(matriz, ruta, restantes, candidatos):
    if len(restantes) == 0:
        faltantes = []
        for i in range(len(ruta) - 1):
            if matriz[ruta[i]][ruta[i + 1]] == 0:
                faltantes.append((ruta[i], ruta[i + 1]))
        if matriz[ruta[-1]][ruta[0]] == 0:
            faltantes.append((ruta[-1], ruta[0]))

        candidatos.append({"ruta": ruta, "faltantes": faltantes})
        return

    actual = ruta[-1]
    for nodo in restantes:
        nuevos_restantes = restantes.copy()
        nuevos_restantes.remove(nodo)
        generar_candidatos_ciclo(matriz, ruta + [nodo], nuevos_restantes, candidatos)


def sugerir_aristas_faltantes(matriz):
    n = len(matriz)
    candidatos = []
    generar_candidatos_ciclo(matriz, [0], list(range(1, n)), candidatos)

    mejor_ruta = None
    mejor_faltantes = None

    for candidato in candidatos:
        faltantes = candidato["faltantes"]
        if mejor_faltantes is None or len(faltantes) < len(mejor_faltantes):
            mejor_ruta = candidato["ruta"]
            mejor_faltantes = faltantes

    return mejor_ruta, mejor_faltantes


# FUERZA BRUTA MEDIANTE RECURSIVIDAD

def calcular_costo(ruta, matriz):
    costo = 0

    for i in range(len(ruta) - 1):
        origen = ruta[i]
        destino = ruta[i + 1]

        if matriz[origen][destino] == 0:
            return None

        costo += matriz[origen][destino]

    return costo


def generar_rutas_FB(ruta, restantes, matriz, soluciones, pasos=None):

    # CASO BASE:
    # Si ya no quedan nodos por visitar,
    # intentamos regresar al nodo inicial.
    if len(restantes) == 0:

        inicio = ruta[0]
        ultimo = ruta[-1]

        # Solo existe un ciclo si el ultimo nodo
        # tiene conexion con el nodo inicial.
        valida = matriz[ultimo][inicio] != 0
        ruta_final = ruta + [inicio]
        costo = calcular_costo(ruta_final, matriz) if valida else None

        # Registra el intento de ruta, valido o no.
        if pasos is not None:
            pasos.append({"ruta": ruta_final, "valida": valida, "costo": costo}) ## append es para agregar un elemento al final de la lista

        # Evita guardar el mismo ciclo recorrido al reves.
        if valida and ruta[1] < ruta[-1]:
            soluciones.append({"ruta": ruta_final, "costo": costo})

        return

    # Nodo donde estamos actualmente.
    actual = ruta[-1]

    # Probamos cada nodo que todavia falta visitar.
    for nodo in restantes:

        # Solo podemos avanzar si existe una arista.
        if matriz[actual][nodo] != 0:

            # Creamos una nueva lista sin el nodo elegido.
            nuevos_restantes = restantes.copy()
            nuevos_restantes.remove(nodo)

            # Continuamos la busqueda desde ese nodo.
            generar_rutas_FB(
                ruta + [nodo],
                nuevos_restantes,
                matriz,
                soluciones,
                pasos
            )
            
#  MERGE SORT 
def merge_sort(lista):
    if len(lista) <= 1:
        return lista

    mitad = len(lista) // 2

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


# FUNCION PRINCIPAL PARA SER UTILIZADA POR LA INTERFAZ

def resolver_tsp(matriz):
   
    n = len(matriz)
    soluciones = []
    pasos = []

    generar_rutas_FB([0], list(range(1, n)), matriz, soluciones, pasos)

    ordenadas = merge_sort(soluciones)

    return {
        "pasos": pasos,
        "soluciones": soluciones,
        "ordenadas": ordenadas,
        "mejor": ordenadas[0] if ordenadas else None,
        "total_evaluadas": len(soluciones),
    }