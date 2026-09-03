# Project Foundry

A reusable foundation for PySide6 and PyVista desktop applications.

The library is organized around reusable models and contracts, with optional Qt and PyVista views. It includes planned foundations for object graphs, block processing, task execution, trees, scene tables, dialogs, serialization, and ready-to-use view templates.

## Development

Create a Python environment, install the package with development dependencies, and run:

```text
pytest
ruff check .
```

## Consumer project setup

Install Project Foundry in a consumer project, then run the instruction setup command from that project root:

```text
projectfoundry-init-instructions
```

Use `--project-root PATH` to target another project, `--check` to inspect the current state, or `--remove` to remove only the managed Project Foundry block. Consumer-specific instructions outside the `<projectfoundry>` markers are preserved.

## Implemented foundations

- Framework-neutral block objects with dependency invalidation and lifecycle callbacks
- Framework-neutral project objects with stable identity and lifecycle callbacks
- Project composition root with UID-backed object, block, and node registries
- Application-scoped ProjectManager singleton with independently testable Projects
- Extensible type registry
- Tree nodes and root manager, including object aliases and block-child projections
- PySide6 tree model and tree dropdown using factory/model/view boundaries
- Scene table row contracts, manager, and Qt model with visibility and removal actions
- Scene table view template with ready-to-use sizing and interaction defaults
- Scene model with selection and visibility state
- PyVista scene adapter with actor membership and visibility management
- PyVista Qt scene view template for quick-start applications
- Qt tree view template with node selection and expansion-state persistence
- Quick-start main-window template composing tree, scene table, and scene views
- Base popup and tab editor dialogs using factory/model/view separation
- Dedicated dialog and tab editor model/view/factory modules inheriting shared editor contracts and mixins
- Qt-free task runner with progress, pause/resume, cancellation, and failure state
- PySide6 task-runner adapter and task table model
- Dependency-aware block-task scheduling with cycle and missing-child checks
- Registry-driven, versioned JSON project serialization with block-graph restoration

Qt dialog, dropdown, tree, table, scene, task runner, serializer, and view templates will be added as explicit layers on top of these foundations.
