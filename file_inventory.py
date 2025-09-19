"""Aplicación para inventariar archivos en un directorio y exportar a Excel.

Este script solicita al usuario una ruta al arrancar, recorre de forma
recursiva todos los archivos presentes y genera un archivo de Excel con las
columnas Nombre, Extensión y Tamaño (en bytes).
"""

from __future__ import annotations

import errno
import os
import stat
import sys
from contextlib import closing
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, List, Optional, Tuple

try:
    from openpyxl import Workbook
except ImportError as exc:  # pragma: no cover - se ejecuta sólo si falta la dependencia
    print(
        "No se encontró la librería 'openpyxl'. Instálala con "
        "'pip install openpyxl' e inténtalo nuevamente.",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


FileRecord = Tuple[Path, str, str, Optional[int]]


def iterar_archivos(directorio: Path) -> Iterator[Path]:
    """Itera recursivamente por todos los archivos dentro de ``directorio``.

    Se omiten enlaces simbólicos a directorios para evitar ciclos infinitos. Los
    errores de permisos y de acceso se notifican al usuario pero no detienen la
    exploración del resto de rutas.
    """

    pendientes: List[Path] = [directorio]
    while pendientes:
        actual = pendientes.pop()
        try:
            for entrada in actual.iterdir():
                try:
                    if entrada.is_symlink():
                        continue
                    if entrada.is_dir():
                        pendientes.append(entrada)
                    elif entrada.is_file():
                        yield entrada
                except OSError as error:
                    print(
                        f"No fue posible procesar '{entrada}': {error.strerror}",
                        file=sys.stderr,
                    )
        except PermissionError as error:
            print(
                f"Permiso denegado al acceder a '{actual}': {error}",
                file=sys.stderr,
            )
        except FileNotFoundError:
            # El directorio puede haber sido eliminado mientras se iteraba.
            continue


def generar_registros(directorio: Path) -> Iterator[FileRecord]:
    """Genera los registros con la información relevante de cada archivo."""

    for archivo in iterar_archivos(directorio):
        extension = archivo.suffix[1:] if archivo.suffix else ""
        try:
            tamanio = os.stat(archivo, follow_symlinks=False).st_size
        except OSError as error:
            mensaje_error = error.strerror or str(error)
            print(
                f"No se pudo obtener el tamaño de '{archivo}': {mensaje_error}",
                file=sys.stderr,
            )
            tamanio = None
        yield archivo, archivo.name, extension, tamanio


def guardar_en_excel(registros: Iterable[FileRecord], destino: BinaryIO) -> int:
    """Escribe un archivo de Excel con los ``registros`` proporcionados."""

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Archivos"
    hoja.append(["Nombre", "Extensión", "Tamaño (bytes)"])

    total_registros = 0
    for _, nombre, extension, tamanio in registros:
        hoja.append([nombre, extension, tamanio])
        total_registros += 1

    hoja.freeze_panes = "A2"
    if total_registros:
        hoja.auto_filter.ref = f"A1:C{total_registros + 1}"
    else:
        hoja.auto_filter.ref = "A1:C1"

    # Ajustamos anchos de columna estimados para mejorar la lectura.
    hoja.column_dimensions["A"].width = 50
    hoja.column_dimensions["B"].width = 15
    hoja.column_dimensions["C"].width = 18

    libro.save(destino)
    return total_registros


def preparar_directorio_salida() -> Path:
    """Crea (si es necesario) un directorio seguro para los reportes."""

    destino_base = Path.home() / "inventarios_archivos"
    try:
        destino_base.mkdir(mode=0o700, parents=True, exist_ok=False)
    except FileExistsError:
        if destino_base.is_symlink() or not destino_base.is_dir():
            raise RuntimeError(
                f"El directorio de salida '{destino_base}' no es seguro."
            )
    else:
        try:
            os.chmod(destino_base, 0o700)
        except OSError:
            pass

    if os.name != "nt":
        try:
            modo_actual = stat.S_IMODE(destino_base.stat().st_mode)
        except OSError as error:
            raise RuntimeError(
                "No se pudo validar la seguridad de "
                f"'{destino_base}': {error.strerror or error}"
            ) from error

        if modo_actual & 0o077:
            raise RuntimeError(
                f"El directorio de salida '{destino_base}' debe ser privado para el usuario."
            )
    else:
        # En Windows los permisos POSIX tradicionales no son significativos.
        # Dejamos un mensaje informativo si el directorio es compartido, pero
        # no bloqueamos la ejecución para no impedir el uso legítimo.
        if not os.access(destino_base, os.W_OK | os.X_OK):
            raise RuntimeError(
                f"No se tiene permiso de escritura en el directorio '{destino_base}'."
            )

    return destino_base


def crear_destino_excel(directorio: Path) -> Tuple[Path, BinaryIO]:
    """Devuelve una ruta y un descriptor seguro donde guardar el Excel."""

    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    identificador = directorio.name or directorio.anchor.replace(":", "") or "raiz"
    nombre_base = f"inventario_archivos_{identificador}_{marca_tiempo}"

    destino_base = preparar_directorio_salida()

    intento = 0
    while True:
        sufijo = "" if intento == 0 else f"_{intento}"
        nombre = f"{nombre_base}{sufijo}.xlsx"
        ruta_destino = destino_base / nombre
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            descriptor = os.open(ruta_destino, flags, 0o600)
        except FileExistsError:
            intento += 1
            continue
        except OSError as error:
            if error.errno == errno.EEXIST:
                intento += 1
                continue
            raise

        archivo = os.fdopen(descriptor, "wb")
        return ruta_destino, archivo


def solicitar_directorio() -> Optional[Path]:
    """Pregunta al usuario por la ruta a analizar y valida que sea correcta."""

    ruta = input("Introduce la ruta a escanear: ").strip()
    if not ruta:
        print("No se proporcionó ninguna ruta.")
        return None

    directorio = Path(ruta).expanduser()
    if not directorio.exists():
        print(f"La ruta '{directorio}' no existe.")
        return None
    if not directorio.is_dir():
        print(f"La ruta '{directorio}' no es un directorio.")
        return None

    return directorio.resolve()


def main() -> None:
    directorio = solicitar_directorio()
    if directorio is None:
        return

    registros = generar_registros(directorio)
    try:
        primer_registro = next(registros)
    except StopIteration:
        print("No se encontraron archivos en la ruta indicada.")
        return

    registros = chain([primer_registro], registros)

    try:
        ruta_destino, archivo_destino = crear_destino_excel(directorio)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return
    except OSError as error:
        mensaje_error = error.strerror or str(error)
        print(
            f"No se pudo preparar el archivo de salida: {mensaje_error}",
            file=sys.stderr,
        )
        return

    with closing(archivo_destino):
        guardar_en_excel(registros, archivo_destino)

    print(f"Inventario generado correctamente en: {ruta_destino}")


if __name__ == "__main__":
    main()
