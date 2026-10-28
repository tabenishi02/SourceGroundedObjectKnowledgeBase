"""Operator-facing Object and Registry application services for Phase M."""

from __future__ import annotations

from dataclasses import asdict

from .domain.object import LifecycleStatus


class ObjectSelectorError(ValueError):
    code = "object_selector_error"


class ObjectAdminApplication:
    """Thin Object Registry application boundary shared by operator clients."""

    def __init__(self, repository):
        self.repository = repository
        self.objects = repository.object_store

    def resolve_object_id(self, *, object_id: str | None = None, name: str | None = None) -> str:
        if bool(object_id) == bool(name):
            raise ObjectSelectorError("Specify exactly one of --object or --name")
        if object_id:
            try:
                return self.objects.get_object(object_id).object_id
            except ValueError as exc:
                raise ObjectSelectorError("Object was not found") from exc

        target = str(name).strip()
        matches = []
        for item in self.objects.list_objects():
            if item.name == target or any(alias.value == target for alias in item.aliases):
                matches.append(item.object_id)
        matches = list(dict.fromkeys(matches))
        if not matches:
            raise ObjectSelectorError("Object name or alias was not found")
        if len(matches) != 1:
            raise ObjectSelectorError("Object name or alias is ambiguous")
        return matches[0]

    def _class_id(self, value: str) -> str:
        record = self.objects.class_by_id(value) or self.objects.class_by_key(value)
        if record is None:
            raise ValueError(f"Unknown Object Class: {value}")
        return record.class_id

    def add_object(self, name: str, primary_class: str, aliases=()) -> dict:
        class_id = self._class_id(primary_class)
        object_id = self.objects.create_object(name, class_id, aliases)
        return asdict(self.objects.get_object(object_id))

    def list_objects(self) -> list[dict]:
        return [asdict(item) for item in self.objects.list_objects()]

    def show_object(self, object_id: str) -> dict:
        return asdict(self.objects.get_object(object_id))

    def show(
        self,
        object_id: str,
        *,
        include_knowledge: bool = False,
        version_id: str | None = None,
    ) -> dict:
        """Return registry-only or combined registry + accepted Knowledge detail."""

        registry = self.show_object(object_id)
        if not include_knowledge:
            return registry
        if registry["current_version_id"] is None and version_id is None:
            return {"registry": registry, "knowledge": None}
        from .application_read import KnowledgeReadApplication

        return {
            "registry": registry,
            "knowledge": KnowledgeReadApplication(self.repository).get_object(
                object_id, version_id=version_id
            ),
        }

    def rename_object(self, object_id: str, name: str) -> dict:
        self.objects.rename_object(object_id, name)
        return asdict(self.objects.get_object(object_id))

    def set_status(self, object_id: str, status: str) -> dict:
        self.objects.set_status(object_id, LifecycleStatus(status))
        return asdict(self.objects.get_object(object_id))

    def aliases(self, object_id: str) -> list[dict]:
        return [asdict(item) for item in self.objects.get_object(object_id).aliases]

    def add_alias(
        self, object_id: str, value: str, *, language: str | None = None, kind: str = "alias"
    ) -> dict:
        alias_id = self.objects.add_alias(object_id, value, language=language, kind=kind)
        return {"object_id": object_id, "alias_id": alias_id, "aliases": self.aliases(object_id)}

    def set_primary_class(self, object_id: str, class_ref: str) -> dict:
        class_id = self._class_id(class_ref)
        self.objects.set_primary_class(object_id, class_id)
        return asdict(self.objects.get_object(object_id))

    def add_class(self, object_id: str, class_ref: str) -> dict:
        class_id = self._class_id(class_ref)
        self.objects.add_additional_class(object_id, class_id)
        return asdict(self.objects.get_object(object_id))

    def remove_class(self, object_id: str, class_ref: str) -> dict:
        class_id = self._class_id(class_ref)
        self.objects.remove_additional_class(object_id, class_id)
        return asdict(self.objects.get_object(object_id))

    def events(self, object_id: str) -> list[dict]:
        return self.objects.registry_events(object_id)

    def classes(self) -> list[dict]:
        return [asdict(item) for item in self.objects.classes()]

    def class_show(self, value: str) -> dict:
        record = self.objects.class_by_id(value) or self.objects.class_by_key(value)
        if record is None:
            raise ValueError("Object Class was not found")
        return asdict(record)

    def relation_types(self) -> list[dict]:
        return [asdict(item) for item in self.objects.relation_types()]

    def relation_type_show(self, value: str) -> dict:
        record = self.objects.relation_type_by_id(value) or self.objects.relation_type_by_key(value)
        if record is None:
            raise ValueError("Relation Type was not found")
        return asdict(record)
