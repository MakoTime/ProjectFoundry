# Current Tasks


- [ ] **P1: Add complete demo integration coverage**
	- Cover new project startup, existing project loading, block/tree creation, editor interaction, task processing, artifact persistence, scene/table display, save/reopen, and shutdown.
	- Run the tests with a QApplication fixture for all Qt-facing tests.
	- Run the full test suite, Ruff, and the manual demo workflow before marking the demo acceptable.


# Future Tasks


# Completed Tasks

- [x] **P1: Harden demo editor and VTK lifecycle**
	- Explicitly clean up mesh preview render windows before dialog destruction.
	- Prevent queued preview renders after close.
	- Cover accept, cancel, validation failure, and destruction paths.

- [x] **P1: Correct demo startup composition**
	- Move root-node discovery/creation out of the main window.
	- Resolve existing project state through Project and application services.
	- Make multiple demo mesh blocks work deterministically.

- [x] **P0: Correct demo processing lifecycle**
	- Preserve prepare, process, commit ordering.
	- Add scene membership only after successful commit.
	- Keep commit, Project events, and scene/table updates on the GUI thread.

- [x] **P0: Complete demo block editor workflows**
	- Support New from a root node, Edit from a tree node, and Edit from a scene-table row.
	- Apply validated name and mesh data through Project-owned operations.
	- Preserve UID-only relationships and remove stale single-item window state.

- [x] **P0: Restore demo application boundaries**
	- Keep `DemoWindow` responsible for Qt composition, commands, selection, and presentation refresh.
	- Move editor workflows into a demo-level controller.
	- Keep project mutations and processing in `DemoProjectService`.

- [x] **P2: Remove UI-owned project orchestration**
	- Keep `DemoWindow` responsible for layout, user commands, and presentation wiring only.
	- Move creation, processing, persistence, and project mutation workflows into project/application services.
	- Keep long-lived state UID-backed and resolve canonical objects through Project at operation boundaries.

- [x] **P1: Add a project-level demo item creation operation**
	- Create and register the block and tree node through the demo application service and Project API.
	- Validate duplicate UIDs, parent UID, cross-project ownership, and all relationships before mutation.
	- Test successful creation and failed operations with no partial state.

- [x] **P1: Complete project and subsystem lifecycle cleanup**
	- Add explicit detach/close behavior for ProjectContext, SceneTableManager block watchers, SceneModel, task services, and scene adapters.
	- Ensure shutdown is idempotent and cannot dispatch callbacks into destroyed Qt or VTK objects.
	- Test repeated close and project replacement.

- [x] **P2: Correct startup composition**
	- Do not re-add existing root nodes or emit events for no-op operations.
	- Establish managers, loaders, adapters, and models in one documented composition order.
	- Restore existing scene entries through explicit loading APIs rather than refresh side effects.

- [x] **P1: Define one canonical demo item composition**
	- Use a documented block-only composition for demo mesh items.
	- Resolve tree, scene, table, task, and serializer relationships through block UIDs.
	- Cover the block-only composition with workflow and Project tests.

- [x] **P1: Rebuild the mesh editor using the dialog contract**
	- Add dedicated `model.py`, `view.py`, and `factory.py` implementations based on `DialogEditorModel`, `DialogEditorView`, and `DialogEditorFactory`.
	- Keep the temporary editor model separate from `DemoMeshBlock`.
	- Have the editor return validated values; let application composition create the domain block through a Project API.
	- Keep PyVista preview resources in the view or a preview adapter, not in the model.
	- Test accept, cancel, validation failure, and dialog destruction.

- [x] **P1: Restore complete serialized demo block data**
	- Reconstruct `DemoMeshData` and `ArtifactMetadata` from the complete serialized record.
	- Preserve artifact path, format, version, checksum, and validity.
	- Add a demo block serialization round-trip test.

- [x] **P1: Make `DemoMeshBlock.prepare()` side-effect free**
	- Validate the requested shape without changing block validity or committed output state.
	- Mark the block valid only from successful `commit()`.
	- Test failed preparation, failed processing, failed persistence, and successful commit behavior.

- [x] **P0: Make task completion and save ordering deterministic**
	- Prevent close while processing, or cancel and drain tasks before saving.
	- Save only after all successful commits and artifact writes have completed.
	- Test close, cancel-close, discard, save, and close-while-processing paths.

- [x] **P0: Fix the accepted create-shape path**
	- Replace the stale `self.block.guid` reference with the block UID returned by the project operation.
	- Add an automated test covering accept, registration, tree insertion, processing, and scene insertion.

- [x] **P0: Keep all VTK and Qt mutations on the GUI thread**
	- Restrict worker threads to `prepare()` and `process()` work.
	- Schedule `commit()`, project events, scene/table refreshes, and adapter actor updates on the Qt thread.
	- Add a regression test that records the thread for task completion and scene updates.

- [x] Add main-window unsaved-change handling
- [x] Add launcher and end-to-end workflow tests
- [x] Document launcher and package workflows
- [x] Load blocks, tree state, and scene/table state through the project context
- [x] Add main-window save and close handling
- [x] Pass opened project context into the main application
- [x] Start the demo with the launcher before the main window
- [x] Add project launcher model, view, and factory
- [x] Add new, recent, and file-open project workflows
- [x] Add the project launcher model for new, recent, and file-open workflows
- [x] Add the project launcher view and factory
- [x] Add the New Project workflow and initial package creation
- [x] Add the Open Recent Project workflow
- [x] Add the Open Project From File workflow
- [x] Return an opened project context from the launcher
- [x] Define the project package format and configurable file extension
- [x] Define the project working-directory and project-context contract
- [x] Implement ZIP project package creation, extraction, validation, and atomic replacement
- [x] Store project metadata and large artifacts inside the project package
- [x] Add application-data storage for recent project references
- [x] Add recent-project cleanup, deduplication, ordering, and display-name handling
- [x] Define project package format and configurable file extension
- [x] Define project working-directory and project-context contract
- [x] Implement ZIP package creation, extraction, validation, and atomic replacement
- [x] Store project metadata and artifacts inside the project package
- [x] Add application-data configurable recent project references
- [x] Add recent-project cleanup, deduplication, ordering, and display-name handling
- [x] Backward-compatible project format migration not required by design
- [x] Remove obsolete ObjectBase scene state and object-centric project serialization behavior
- [x] Update package exports and documentation
- [x] Run focused tests, the full test suite, and Ruff
- [x] Update package exports and documentation
- [x] Run focused tests, the full test suite, and Ruff
- [x] Define scene object created, removed, refreshed, and block output events
- [x] Emit lifecycle events only after successful state changes
- [x] Make the renderer own actors only and respond to scene/table events
- [x] Refresh and remove renderer actors with scene object lifecycle events
- [x] Ensure temporary editor objects are never serialized
- [x] Remove direct scene membership ownership from Project
- [x] Create temporary scene objects in the scene/table manager when blocks are added
- [x] Restore scene/table state and scene objects during project startup
- [x] Fetch mesh, line, and shape artifacts through block_uid
- [x] Release scene objects and loaded shape data during project shutdown
- [x] Add scene/table lifecycle and project-startup restoration tests
- [x] Ensure blocks do not create or destroy scene objects
- [x] Keep persistent scene/table references as block_uid values
- [x] Keep scene object, tree node, and table row identities separate from block_uid
- [x] Redefine ObjectBase as a temporary editor object created from block_data
- [x] Apply validated editor changes back to the relevant block
- [x] Destroy editor objects after apply, cancel, or editor close
- [x] Make one coupled scene/table manager own scene/table runtime state
- [x] Make Project the intermediary for UID-based scene requests
- [x] Route tree, block, and table scene requests through Project.add_to_scene()
- [x] Resolve node, block, and table UIDs through Project registries before delegation
- [x] Delegate validated scene requests from Project to the coupled scene/table manager
- [x] Create temporary scene objects in the scene/table manager when blocks are added
- [x] Validate block_uid references and load blocks before dependent state
- [x] Add project load rollback for the new structure
- [x] Release processed shape data from memory after successful persistence
- [x] Add lazy artifact loading through block_uid
- [x] Add block output, invalidation, and artifact lifecycle tests
- [x] Make blocks and block_data the primary serialized project data
- [x] Serialize block relationships, tree state, and scene/table state separately
- [x] Store block_uid references in tree and scene/table records
- [x] Define persistent BlockObject block_data and separate disk-backed shape artifacts
- [x] Define artifact metadata: path, format, version, checksum, and validity
- [x] Persist processed block outputs atomically during commit()
- [x] Preserve the previous valid artifact when processing or persistence fails
- [x] Migrate SceneModel to project-backed UID storage
- [x] Migrate TableManager and SceneTableModel to project UID references
- [x] Migrate TaskRunner block bindings to project UID resolution
- [x] Migrate TreeManager and TreeModel mutations through Project
- [x] Integrate ProjectSerializer with phased Project loading and validation
- [x] Add Project event notifications and subsystem synchronization
- [x] Build cross-subsystem integration tests for one complete item
- [x] Run full regression, lint, and package validation
- [x] Add managed Project Foundry instruction propagation command
- [x] Add quick release launcher with version bump, changelog, commit, tag, and push options
