from pydantic import BaseModel, ConfigDict


class SaludPublic(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"estado": "ok"}]})

    estado: str
