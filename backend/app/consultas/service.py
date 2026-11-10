from collections import Counter
from typing import get_args

from fastapi import HTTPException, status
from sqlalchemy import RowMapping
from sqlmodel import Session

from app.acceso import repository as acceso_repository
from app.acceso.schema import UsuarioPublic
from app.acceso.service import unidades_visibles
from app.movimientos.service import AREA_DEL_TIPO
from app.organizacion.model import Nivel

from . import repository
from .schema import (
    ActaDemorada,
    BienInventarioPublic,
    Etapa,
    GrupoSituacion,
    HistorialBienPublic,
    SituacionPublic,
    TipoSituacion,
    UnidadSituacion,
)


def consultar_inventario(
    session: Session,
    usuario: UsuarioPublic,
    unidad_id: int | None,
    tipo_bien: str | None,
) -> list[BienInventarioPublic]:
    unidades = [unidad.id for unidad in unidades_visibles(session, usuario)]
    if unidad_id is not None:
        if unidad_id not in unidades:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso al inventario de esa unidad",
            )
        unidades = [unidad_id]
    filas = repository.listar_inventario(session, unidades, tipo_bien)
    return [BienInventarioPublic.model_validate(fila) for fila in filas]


def consultar_historial(
    session: Session, usuario: UsuarioPublic, bien_id: int
) -> HistorialBienPublic:
    bien = repository.buscar_bien(session, bien_id)
    if bien is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El bien no existe"
        )
    visibles = {unidad.id for unidad in unidades_visibles(session, usuario)}
    if bien["unidad_id"] not in visibles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso al historial de ese bien",
        )
    eventos = repository.listar_historial(session, bien_id)
    return HistorialBienPublic.model_validate(
        {"bien": dict(bien), "eventos": [dict(evento) for evento in eventos]}
    )


def unidades_de_la_sala(
    session: Session, usuario: UsuarioPublic, regional_id: int | None
) -> list[int]:
    nivel = usuario.unidad.nivel
    if nivel == Nivel.OPERACIONAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La sala de situación es para la Regional y la Dirección",
        )
    if regional_id is None:
        return [unidad.id for unidad in unidades_visibles(session, usuario)]
    if nivel != Nivel.DIRECCION:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Solo la Dirección elige una Regional",
        )
    unidades = acceso_repository.listar_unidad_y_dependientes(session, regional_id)
    elegida = next((unidad for unidad in unidades if unidad.id == regional_id), None)
    if elegida is None or elegida.nivel != Nivel.REGIONAL:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La unidad elegida no es una Regional",
        )
    return [unidad.id for unidad in unidades]


def orden_jerarquico(fila: RowMapping) -> tuple[int, int, int]:
    if fila["nivel"] == Nivel.DIRECCION:
        return (0, 0, 0)
    if fila["nivel"] == Nivel.REGIONAL:
        return (1, fila["id"], 0)
    return (1, fila["unidad_superior_id"], fila["id"])


def conteo(
    bienes: dict[tuple[int, str], RowMapping], unidad_id: int, tipo: str
) -> TipoSituacion:
    fila = bienes.get((unidad_id, tipo))
    return TipoSituacion(
        tipo_bien=tipo,
        total=int(fila["total"]) if fila else 0,
        fuera_de_servicio=int(fila["fuera_de_servicio"]) if fila else 0,
    )


def consultar_situacion(
    session: Session, usuario: UsuarioPublic, regional_id: int | None
) -> SituacionPublic:
    alcance = unidades_de_la_sala(session, usuario, regional_id)
    filas = sorted(
        repository.listar_unidades_del_alcance(session, alcance), key=orden_jerarquico
    )
    bienes = {
        (fila["unidad_id"], fila["tipo_bien"]): fila
        for fila in repository.contar_bienes_por_unidad(session, alcance)
    }
    actas = repository.listar_actas_abiertas(session, alcance)
    abiertas = Counter(acta["unidad_id"] for acta in actas)
    unidades = [
        UnidadSituacion(
            id=fila["id"],
            nombre=fila["nombre"],
            nivel=fila["nivel"],
            tipos=[conteo(bienes, fila["id"], tipo) for tipo in AREA_DEL_TIPO],
            abiertas=abiertas[fila["id"]],
        )
        for fila in filas
    ]
    grupos = []
    for etapa in get_args(Etapa):
        del_grupo = [acta["dias"] for acta in actas if acta["etapa"] == etapa]
        grupos.append(
            GrupoSituacion(
                etapa=etapa,
                cantidad=len(del_grupo),
                dias_mas_antigua=max(del_grupo) if del_grupo else None,
            )
        )
    demoradas = [ActaDemorada.model_validate(dict(acta)) for acta in actas[:5]]
    return SituacionPublic(unidades=unidades, grupos=grupos, demoradas=demoradas)
