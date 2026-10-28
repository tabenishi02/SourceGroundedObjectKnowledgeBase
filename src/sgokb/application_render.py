"""Transport-neutral Markdown render application."""

from __future__ import annotations

from pathlib import Path

from .rendering import DEFAULT_RENDER_ROOT, MarkdownRenderService


class RenderApplication:
    def __init__(self, repository) -> None:
        self.repository = repository

    def render(
        self,
        *,
        object_id: str | None = None,
        version_id: str | None = None,
        output_root: str | Path = DEFAULT_RENDER_ROOT,
    ):
        if bool(object_id) == bool(version_id):
            raise ValueError("Specify exactly one of Object or Version to render")
        resolved_version = version_id
        if resolved_version is None:
            resolved_version = self.repository.version_store.current_version_id(object_id)
            if resolved_version is None:
                raise ValueError("Object has no current accepted Version to render")
        return MarkdownRenderService(self.repository).render_version(
            resolved_version, output_root=Path(output_root)
        )
