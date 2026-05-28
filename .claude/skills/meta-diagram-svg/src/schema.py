from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GroupKind(str, Enum):
    cloud = "cloud"
    onprem = "onprem"
    partner = "partner"
    saas = "saas"
    internal = "internal"
    generic = "generic"


class ComponentType(str, Enum):
    channel = "channel"
    gateway = "gateway"
    mainframe = "mainframe"
    server = "server"
    core_engine = "core_engine"
    external_partner = "external_partner"
    datastore = "datastore"
    queue = "queue"
    actor = "actor"


class LifecycleStatus(str, Enum):
    unchanged = "unchanged"
    updated = "updated"
    new = "new"


class ConnectionStatus(str, Enum):
    existing = "existing"
    new = "new"


class ProtocolKind(str, Enum):
    sync = "sync"
    async_ = "async"
    data = "data"


PROTOCOL_KIND_MAP = {
    "REST": ProtocolKind.sync,
    "SOAP": ProtocolKind.sync,
    "HTTPS": ProtocolKind.sync,
    "gRPC": ProtocolKind.sync,
    "MQ": ProtocolKind.async_,
    "MQ/XML": ProtocolKind.async_,
    "Kafka": ProtocolKind.async_,
    "Publish": ProtocolKind.async_,
    "Subscribe": ProtocolKind.async_,
    "SFTP": ProtocolKind.data,
    "SMTP": ProtocolKind.data,
    "XML": ProtocolKind.data,
}


class Group(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    parent: Optional[str] = None
    kind: GroupKind = GroupKind.generic


class Component(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    group: Optional[str] = None
    type: ComponentType = ComponentType.server
    lifecycle_status: LifecycleStatus = LifecycleStatus.unchanged


class Connection(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    from_: str = Field(alias="from")
    to: str
    protocol: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.existing

    @property
    def protocol_kind(self) -> ProtocolKind:
        if not self.protocol:
            return ProtocolKind.sync
        return PROTOCOL_KIND_MAP.get(self.protocol, ProtocolKind.sync)


class Diagram(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    groups: list[Group] = []
    components: list[Component] = []
    connections: list[Connection] = []

    @model_validator(mode="after")
    def _validate_refs(self) -> "Diagram":
        group_ids = {g.id for g in self.groups}
        comp_ids = {c.id for c in self.components}

        for g in self.groups:
            if g.parent and g.parent not in group_ids:
                raise ValueError(f"Group '{g.id}' references unknown parent '{g.parent}'")

        for c in self.components:
            if c.group and c.group not in group_ids:
                raise ValueError(f"Component '{c.id}' references unknown group '{c.group}'")

        for conn in self.connections:
            if conn.from_ not in comp_ids:
                raise ValueError(f"Connection from '{conn.from_}' references unknown component")
            if conn.to not in comp_ids:
                raise ValueError(f"Connection to '{conn.to}' references unknown component")

        return self

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Diagram":
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
