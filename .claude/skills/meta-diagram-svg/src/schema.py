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


class Location(str, Enum):
    """Optional, soft 3x3 compass anchor for macro placement.

    Decomposes into a horizontal band (west / none / east -> ELK layer constraint)
    and a vertical band (north / middle / south -> in-layer y-seed). A coarse hint,
    not an exact grid: tagged nodes are *pulled* toward their region; untagged nodes
    flow naturally.
    """
    north_west = "north_west"
    north = "north"
    north_east = "north_east"
    west = "west"
    center = "center"
    east = "east"
    south_west = "south_west"
    south = "south"
    south_east = "south_east"


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
    location: Optional[Location] = None


class Component(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    group: Optional[str] = None
    type: ComponentType = ComponentType.server
    lifecycle_status: LifecycleStatus = LifecycleStatus.unchanged
    location: Optional[Location] = None


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

        # Connection endpoints now resolve against the union of both id-spaces, so an id
        # shared by a group and a component would be ambiguous. Forbid the collision.
        shared = group_ids & comp_ids
        if shared:
            raise ValueError(
                f"id(s) used by both a group and a component (must be unique): "
                f"{sorted(shared)}"
            )

        for g in self.groups:
            if g.parent and g.parent not in group_ids:
                raise ValueError(f"Group '{g.id}' references unknown parent '{g.parent}'")

        for c in self.components:
            if c.group and c.group not in group_ids:
                raise ValueError(f"Component '{c.id}' references unknown group '{c.group}'")

        # A connection endpoint may be a component OR a group (a group endpoint attaches
        # the edge to the group's boundary).
        endpoint_ids = comp_ids | group_ids
        for conn in self.connections:
            if conn.from_ not in endpoint_ids:
                raise ValueError(
                    f"Connection from '{conn.from_}' references unknown component or group"
                )
            if conn.to not in endpoint_ids:
                raise ValueError(
                    f"Connection to '{conn.to}' references unknown component or group"
                )

        return self

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Diagram":
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
