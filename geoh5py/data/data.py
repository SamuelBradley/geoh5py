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

from __future__ import annotations

from abc import abstractmethod

from ..shared import Entity
from .data_association_enum import DataAssociationEnum
from .data_type import DataType
from .primitive_type_enum import PrimitiveTypeEnum


class Data(Entity):
    """
    Base class for Data entities.
    """

    _attribute_map = Entity._attribute_map.copy()
    _attribute_map.update({"Association": "association"})
    _visible = False

    def __init__(
        self,
        data_type: DataType,
        **kwargs,
    ):
        self._association = None
        self._on_file = False
        assert data_type is not None
        assert data_type.primitive_type == self.primitive_type()
        self.entity_type = data_type
        self._values = None

        super().__init__(**kwargs)

        if self.entity_type.name == "Entity":
            self.entity_type.name = self.name

        data_type.workspace._register_data(self)

    @property
    def n_values(self) -> int | None:
        """
        :obj:`int`: Number of expected data values based on
        :obj:`~geoh5py.data.data.Data.association`
        """
        if self.association is DataAssociationEnum.VERTEX:
            return self.parent.n_vertices
        if self.association is DataAssociationEnum.CELL:
            return self.parent.n_cells
        if self.association is DataAssociationEnum.FACE:
            return self.parent.n_faces
        if self.association is DataAssociationEnum.OBJECT:
            return 1

        return None

    @property
    def values(self):
        """
        Data values
        """
        return self._values

    @property
    def association(self) -> DataAssociationEnum | None:
        """
        :obj:`~geoh5py.data.data_association_enum.DataAssociationEnum`:
        Relationship made between the
        :func:`~geoh5py.data.data.Data.values` and elements of the
        :obj:`~geoh5py.shared.entity.Entity.parent` object.
        Association can be set from a :obj:`str` chosen from the list of available
        :obj:`~geoh5py.data.data_association_enum.DataAssociationEnum` options.
        """
        return self._association

    @association.setter
    def association(self, value: str | DataAssociationEnum):
        if isinstance(value, str):

            if value.upper() not in DataAssociationEnum.__members__:
                raise ValueError(
                    f"Association flag should be one of {DataAssociationEnum.__members__}"
                )

            value = getattr(DataAssociationEnum, value.upper())

        if not isinstance(value, DataAssociationEnum):
            raise TypeError(f"Association must be of type {DataAssociationEnum}")

        self._association = value

    @property
    def entity_type(self) -> DataType:
        """
        :obj:`~geoh5py.data.data_type.DataType`
        """
        return self._entity_type

    @entity_type.setter
    def entity_type(self, data_type: DataType):

        self._entity_type = data_type
        self.workspace.update_attribute(self, "entity_type")

    @classmethod
    @abstractmethod
    def primitive_type(cls) -> PrimitiveTypeEnum:
        ...

    def add_file(self, file: str):
        """
        Alias not implemented from base Entity class.
        """
        raise NotImplementedError("Data entity cannot contain files.")
