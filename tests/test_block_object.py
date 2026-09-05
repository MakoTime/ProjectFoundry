from projectfoundry.core import ArtifactMetadata, ArtifactStore, BlockData, BlockObject


class ExampleBlockData(BlockData):
    threshold: float


class ExampleBlock(BlockObject):
    def prepare(self):
        return None

    def process(self, prepared, progress_callback=None):
        return prepared

    def serialise(self, path):
        del path

    def persist_result(self, result, path):
        with open(path, "wb") as artifact:
            artifact.write(result)


class ReleasingBlock(ExampleBlock):
    released = None

    def retain_result(self, result):
        return False

    def release_result(self, result):
        self.released = result


def test_change_invalidates_parents_and_calls_callbacks():
    child = ExampleBlock("child")
    parent = ExampleBlock("parent")
    parent.add_child_block_object(child)
    changes = []
    parent.add_change_callback(changes.append)

    child.mark_changed()

    assert not child.is_valid()
    assert not parent.is_valid()
    assert changes == [parent]


def test_dependent_parent_is_destroyed_with_child():
    child = ExampleBlock("child")
    parent = ExampleBlock("parent")
    parent.add_child_block_object(child, dependent=True)

    child.destroy()

    assert parent.is_destroyed()
    assert child.child_block_objects == ()


def test_block_data_is_validated_and_json_serializable():
    block = ExampleBlock(
        "example",
        block_data=ExampleBlockData(
            threshold="0.5",
            artifact=ArtifactMetadata(path="artifacts/example.vtk", format="vtk"),
        ),
    )

    assert block.block_data.threshold == 0.5
    assert block.serialise_data() == {
        "threshold": 0.5,
        "artifact": {
            "path": "artifacts/example.vtk",
            "format": "vtk",
            "version": 1,
            "checksum": None,
            "valid": True,
        },
    }


def test_artifact_store_writes_atomically_and_loads(tmp_path):
    store = ArtifactStore(tmp_path)

    checksum = store.write_atomic("mesh.bin", lambda path: path.write_bytes(b"mesh"))

    assert (tmp_path / "mesh.bin").read_bytes() == b"mesh"
    assert checksum == store.checksum(tmp_path / "mesh.bin")
    assert store.load("mesh.bin", lambda path: path.read_bytes()) == b"mesh"


def test_artifact_store_preserves_existing_artifact_on_write_failure(tmp_path):
    store = ArtifactStore(tmp_path)
    store.write_atomic("mesh.bin", lambda path: path.write_bytes(b"original"))

    def fail(path):
        path.write_bytes(b"partial")
        raise RuntimeError("write failed")

    try:
        store.write_atomic("mesh.bin", fail)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Failed artifact writes must propagate their error")

    assert (tmp_path / "mesh.bin").read_bytes() == b"original"


def test_commit_persists_result_before_updating_artifact_metadata(tmp_path):
    block = ExampleBlock(
        "example",
        block_data=ExampleBlockData(
            threshold=0.5,
            artifact=ArtifactMetadata(path="mesh.bin", format="bin"),
        ),
    )
    store = ArtifactStore(tmp_path)

    block.commit(b"mesh", store)

    assert (tmp_path / "mesh.bin").read_bytes() == b"mesh"
    assert block.block_data.artifact.valid
    assert block.block_data.artifact.checksum == store.checksum(tmp_path / "mesh.bin")


def test_block_can_release_processed_result_after_commit():
    block = ReleasingBlock("example")

    assert not block.retain_result(b"mesh")
    block.release_result(b"mesh")

    assert block.released == b"mesh"
