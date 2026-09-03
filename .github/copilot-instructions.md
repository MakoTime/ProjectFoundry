# Project Foundry development instructions

<projectfoundry>
## Architecture

- Treat `Project` as the authoritative composition root for one project.
- Keep `Project` independently constructible for tests and tooling.
- Use `ProjectManager` for application-level active-project or singleton behavior.
- Registries own canonical objects, blocks, and nodes; subsystems own references and projections.
- Route add, remove, connect, rename, scene, and task mutations through `Project` APIs.
- Base classes may expose ergonomic methods, but those methods must delegate to `Project`.
- Do not let views, Qt models, or adapters mutate registries or persistent relationships directly.

## UID relationships

- Store long-lived relationships as UIDs, never as object references.
- Resolve related objects through `Project` or a project-owned registry at the point of use.
- Use UIDs for object-to-block, object-to-node, tree, scene, table, task, and serializer relationships.
- Reject duplicate UIDs, missing UIDs, cross-project references, and invalid relationships clearly.
- Validate relationships before mutating either side; failed operations should leave state unchanged.
- Temporary local object references are acceptable inside one operation, task, or callback.
- Serialization must persist UIDs, not memory addresses or runtime UI objects.

## Block objects

- `prepare()` gathers and validates processing inputs without mutating committed output state.
- `process(prepared, progress_callback)` performs computation from prepared inputs.
- `process()` must not mutate registries, tree state, scene state, or committed block output.
- `commit(result)` is the only processing phase that updates committed block state.
- Run `commit()` only after successful processing; failed processing must not partially commit.
- A successful commit validates the block; invalid dependencies must be processed first.
- Detect missing block tasks and dependency cycles before execution.
- Child and parent block relationships must be created through `Project` or inherited project-aware methods.

## Dialogs and mixins

- Every dialog feature has separate `model.py`, `view.py`, and `factory.py` modules.
- Popup/dialog editors and tab editors have separate model, view, and factory implementations.
- Dialog and tab models inherit their appropriate base editor model.
- Dialog and tab views inherit the shared editor view contract and their native Qt widget.
- Use mixins for shared apply, close, button-box, naming, and editor behavior.
- Models contain domain state, validation, and Project interaction.
- Views contain Qt widgets, layout, and widget-to-model synchronization.
- Factories construct and configure the correct model/view presentation.
- Dialogs must not create or register domain items directly when a Project API exists.

## Dependency direction

- Keep the import graph one-way: core, models, adapters, views, then application composition.
- `core` must not import PySide6, PyVista, views, dialogs, or application modules.
- Tree, scene, table, task, and dialog models may depend on core and `Project`.
- Qt models may depend on core and subsystem models, but not on views.
- PySide6 and PyVista code belongs in explicit adapters, views, or templates.
- PyVista adapters own runtime actors, not canonical domain objects.
- Factories may import their views; views must not import their factories.
- Use protocols or small contracts at subsystem boundaries to avoid circular imports.
- Application composition is responsible for wiring Project, models, adapters, views, and dialogs together.

## Tree, scene, and table

- `TreeManager` owns tree roots and hierarchy; `TreeNode` stores UID relationships.
- `TreeModel` delegates edits and mutations through `Project`.
- `SceneModel` stores scene membership and selection by UID when project-backed.
- `TableManager` stores scene rows keyed by object UID when project-backed.
- Scene and table models resolve canonical objects through `Project` when presenting data.
- Actors, Qt indexes, and table rows are runtime projections and are not canonical ownership.

## Events and lifecycle

- Emit Project events only after successful mutations.
- Events identify affected UIDs and related UIDs where applicable.
- Do not emit success events for failed or rolled-back operations.
- Subsystems must unsubscribe from a Project when it is replaced or shut down.
- Removal must clean dependent tree, scene, table, task, block, and UID references.
- Repeated removal and destruction should be deterministic and harmless where practical.

## Testing

- Add focused tests for lifecycle, dependency, serialization, ownership, UID, and model behavior.
- Test success, failure, cancellation, invalidation, duplicate UID, missing reference, cycle, and cross-project cases.
- Test both standalone compatibility and project-backed paths during migrations.
- Add integration coverage for one complete item across object, block, node, scene, table, task, dialog, and serializer layers.
- Run the full test suite and Ruff before marking a task complete.
- Do not mark a task complete until relevant focused tests and full regression checks pass.

</projectfoundry>