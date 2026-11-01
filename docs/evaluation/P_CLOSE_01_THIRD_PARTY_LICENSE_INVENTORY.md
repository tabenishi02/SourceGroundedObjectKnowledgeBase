# P-CLOSE-01 — Third-Party Dependency / License Inventory

Updated: 2026-10-31

- Scope: SGOKB `2.0.0` source/repository release integration
- Authority for dependency versions: `pyproject.toml`
- Binary packaging authority: `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`
- Disposition: **Inventory complete for source release / packaged-binary audit remains separate**

## 1. Direct dependency inventory

| Dependency group | Package | Declared range | Role | P-CLOSE disposition |
|---|---|---:|---|---|
| core | beautifulsoup4 | `>=4.12,<5` | HTML/source processing | source dependency recorded |
| core | httpx | `>=0.27,<1` | HTTP/runtime probes | source dependency recorded |
| core | jsonschema | `>=4.18,<5` | schema validation | source dependency recorded |
| dev | pytest | `>=8,<10` | tests | development-only |
| dev | ruff | `>=0.9,<1` | lint | development-only |
| mcp | mcp | `>=2,<3` | MCP stdio integration | optional dependency recorded |
| gui | PySide6 | `>=6.12,<6.13` | Qt desktop GUI | optional; P-GUI-02 license gate applies |
| local-embedding | torch | `>=2.6,<3` | local model execution | optional dependency recorded |
| local-embedding | sentence-transformers | `>=6.1,<7` | embedding provider | optional dependency recorded |
| local-embedding | transformers | `>=5.2,<6` | model/runtime support | optional dependency recorded |
| fast-embedding | fastembed | `>=0.9,<1` | optional embedding backend | optional dependency recorded |
| vector-qdrant | qdrant-client | `>=1.19,<2` | Qdrant client | optional dependency recorded |

This inventory is intentionally derived from the repository dependency authority rather than from one workstation's currently installed transitive closure.

## 2. GUI / Qt license boundary

P-GUI-02 already accepted the following distribution constraints for PySide6/Qt:

- LGPL/commercial obligations must be handled explicitly for redistribution;
- the accepted initial packaging form is a standalone directory with dynamic Qt shared libraries;
- static Qt linking is outside the accepted baseline;
- packaged artifacts require license texts/notices and source-availability or written-offer instructions as applicable;
- the application must not prevent replacement/relinking of LGPL-covered Qt libraries;
- exact bundled Qt modules and third-party libraries must be audited from the final artifact.

P-CLOSE-01 does not supersede those requirements.

## 3. SGOKB project-license boundary

At the original `2.0.0` P-CLOSE-01 closure on 2026-10-31, the project license had not yet been selected. This condition was superseded on 2026-11-01.

SGOKB source code is licensed under the MIT License, copyright (c) 2026 tabenishi02. The authoritative project-license text is the repository root `LICENSE` file, and `pyproject.toml` declares the MIT license in project metadata.

This project-license decision does not by itself certify a standalone GUI binary distribution. A later public binary artifact still requires an artifact-specific third-party redistribution audit, including the PySide6/Qt obligations described above.

## 4. Transitive dependency rule

A future packaged artifact must generate its license inventory from the **actual frozen artifact/environment**, not only from this direct-dependency table.

Required artifact-time evidence includes:

```text
package name
exact version
source/upstream identity
license metadata / bundled LICENSE files
whether included in the distributed artifact
Qt module/plugin inventory where applicable
required notice/source-offer action
```

Transitive dependencies are not certified by this P-CLOSE source-release inventory.

## 5. P-CLOSE disposition

```text
direct dependency inventory         = Complete
PySide6/Qt redistribution decision = Reused from P-GUI-02
standalone GUI binary publication  = Out of P-CLOSE source-release scope
project license selection          = MIT / accepted 2026-11-01 / copyright tabenishi02
artifact transitive license audit  = Required before future binary publication
```
