# Project Foundry Demo

This is a direct-run manual integration application. It is intentionally outside
`src/projectfoundry` and has no package marker, so it is not part of the library
API or wheel.

From the repository root:

```powershell
.venv\Scripts\python.exe demo\main.py
```

The demo exercises the tree, task runner, coupled scene/table manager, PyVista
scene, project UID routing, and temporary scene-object lifecycle.

The demo uses a block-only composition: each mesh is a registered `DemoMeshBlock`
identified by its block UID. Tree nodes reference block UIDs directly, and scene,
table, task, and serializer state resolve those UIDs through `Project`. Temporary
dialog drafts are not project items and are never serialized.

Right-click a tree node to open its action menu. Double-clicking a mesh node
also adds it to the scene.