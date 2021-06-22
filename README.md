# Proyecto De Sistemas Distribuidos - DScraPy

## Autores

<!--```-->
    - Alejandro Klever Clemente C411
    - Laura Tamayo Blanco C411
<!--```-->

DScraPy (Distributed Scraper in Python) es un sistema de scraping distribuido con un manejo de cache de las url la informacion que busca en la web dado una url.

El proyecto tiene 2 capas principales. La primera es una la capa de usuario que se encarga de atender las demandas del usuario y las segunda es la gestion de la cache de forma descentralizada.

Para la creacion de este sistema hemos usado las bibliotecas:

- `Pyro5` para gestionar la comunicacion entre los diferentes recursos
- `requests` para la obtencion del html de la pagina asociada al url
- `typer` para creacion una cli api que nos permita controlar nuestro sistema y ver informacion de este

### Vista General

Como todo sistema distribuido los nodos la comunicacion entre nodos es fundamental. En DScraPy contamos con 3 tipos de nodos:

- `ClientNode`: Encargados de aceptar las peticiones de los usuarios. Este recibe una lista de url y hace peticiones en demanda al los `RouterNodes` en caso de que la informacion de la url no este almacenada en la DHT.

- `RouterNode`: Su funcion es simplemente manejar la biblioteca de requests para obtener la info de la url.

- `ChordNode`: Los nodos encargados de la gestionar los recursos cacheados asi como la comunicacion entre los diferentes nodos del anillo de chord.

### Sistema de cache

Hemos implementado el Algoritmo y Protocolo de Comunicacion Chords para gestionar la cache del sistema como una tabla de hash decentralizada.

La implementacion realizada utiliza una establilizacionperiodica como medida de tolerancia a fallas, y al almacenarun conjunto de llaves en un nodo tambien se almacenaran en su sucesor para que en el caso de que algun nodo sedesconecte de la red la info almacenanda no se pierda (esta tecnica es extensible al almacenar la info de un node en k sucesores).

Con todo esto en mente podemos darnos cuenta de que sin importar que hayan problemas en los nodos, o estos sean eliminados o agregados la informacion se mantendra consistente.

El algoritmo de hash utilizado es `md5` de la biblioteca `hashlib` de python.

### CLI API

Para crear e interactuar con un sistema montado con DScraPy hemos creado una cli API que es el archivo `main.py`. Al ejecutar `python main.py --help` veremos algo como esto:

```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.

  --help                          Show this message and exit.

Commands:
  create-chord-node
  create-client-node
  create-router-node
  disconnect-chord-node
  finger-table
  hash-table
  start-name-service
```

Para ver como usar cada uno de los comandos tan solo escriba `python main.py [COMMAND] --help`.

Por ultimo decir que el tamaño del chord ring puede ser modificado cambiando la variable `CHORD_RING_SIZE` del archivo `main.py`, por defecto y para el ejemplo es 3, lo que implica que el tamaño del anillo sera de 8 nodos.

### Testing

En el archivo `test_system.py` crea un sistema sencillo de 3 nodos chords en un sistema de tamaño 8 y se realizan los request de las url puestas en una lista dentro del ejemplo. Luego se eliminan los nodos prograsivamente y se van imprimendo las finger tables, asi como la llaves asociadas a cada nodo.
