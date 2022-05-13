#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of geoh5py.
#
#  geoh5py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  geoh5py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with geoh5py.  If not, see <https://www.gnu.org/licenses/>.


import numpy as np

from geoh5py.objects import Surface
from geoh5py.shared.utils import compare_entities
from geoh5py.workspace import Workspace


def test_create_surface_data(tmp_path):
    h5file_path = tmp_path / r"testSurface.geoh5"

    with Workspace(h5file_path) as workspace:
        # Create a grid of points and triangulate
        x, y = np.meshgrid(np.arange(10), np.arange(10))
        x, y = x.ravel(), y.ravel()
        z = np.random.randn(x.shape[0])

        xyz = np.c_[x, y, z]

        simplices = np.unique(
            np.random.randint(0, xyz.shape[0] - 1, (xyz.shape[0], 3)), axis=1
        )

        # Create random data
        values = np.mean(
            np.c_[x[simplices[:, 0]], x[simplices[:, 1]], x[simplices[:, 2]]], axis=1
        )

        # Create a geoh5 surface
        surface = Surface.create(
            workspace, name="mySurf", vertices=xyz, cells=simplices
        )

        data = surface.add_data({"TMI": {"values": values}})

        # Read the object from a different workspace object on the same file
        new_workspace = Workspace(h5file_path)

        rec_obj = new_workspace.get_entity("mySurf")[0]
        rec_data = rec_obj.get_data("TMI")[0]

        compare_entities(surface, rec_obj)
        compare_entities(data, rec_data)
