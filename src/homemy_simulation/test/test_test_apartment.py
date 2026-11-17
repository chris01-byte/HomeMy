"""The synthetic apartment must be a valid OccupancyGrid and grow as described."""

from homemy_simulation import test_apartment


def test_full_map_has_expected_size_and_values():
    cells = test_apartment.build_cells()
    assert len(cells) == test_apartment.WIDTH * test_apartment.HEIGHT
    assert set(cells) <= {-1, 0, 100}
    assert cells.count(0) > 0 and cells.count(100) > 0


def test_revision_changes_the_map():
    assert test_apartment.build_cells(0) != test_apartment.build_cells(1)


def test_partial_reveal_hides_the_rest():
    partial = test_apartment.build_cells(1, reveal_columns=14)
    full = test_apartment.build_cells(1)
    assert partial.count(-1) > full.count(-1)
    for y in range(test_apartment.HEIGHT):
        row = partial[y * test_apartment.WIDTH:(y + 1) * test_apartment.WIDTH]
        assert all(value == -1 for value in row[14:])
