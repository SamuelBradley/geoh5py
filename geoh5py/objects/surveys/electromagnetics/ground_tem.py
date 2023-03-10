#  Copyright (c) 2023 Mira Geoscience Ltd.
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

# pylint: disable=too-many-locals, too-many-branches

from __future__ import annotations

import uuid

import numpy as np

from geoh5py.data import ReferencedData
from geoh5py.objects import Curve
from geoh5py.objects.object_base import ObjectType

from .base import BaseTEMSurvey


class BaseGroundTEM(BaseTEMSurvey, Curve):  # pylint: disable=too-many-ancestors
    __INPUT_TYPE = ["Tx and Rx"]
    _tx_id_property: ReferencedData | None = None

    def copy(
        self,
        parent=None,
        copy_children: bool = True,
        clear_cache: bool = False,
        mask: np.ndarray | None = None,
        cell_mask: np.ndarray | None = None,
        **kwargs,
    ):
        """
        Function to copy a survey to a different parent entity.

        :param parent: Target parent to copy the entity under. Copied to current
            :obj:`~geoh5py.shared.entity.Entity.parent` if None.
        :param copy_children: Create copies of all children entities along with it.
        :param clear_cache: Clear array attributes after copy.
        :param mask: Array of indices to sub-sample the input entity.
        :param cell_mask: Array of indices to sub-sample the input entity cells.
        :param kwargs: Additional keyword arguments.

        :return: New copy of the input entity.
        """
        if parent is None:
            parent = self.parent

        omit_list = [
            "_metadata",
            "_receivers",
            "_transmitters",
            "_base_stations",
            "_tx_id_property",
        ]
        metadata = self.metadata.copy()
        if mask is not None and self.vertices is not None:
            if not isinstance(mask, np.ndarray) or mask.shape != (
                self.vertices.shape[0],
            ):
                raise ValueError("Mask must be an array of shape (n_vertices,).")

        new_entity = super().copy(
            parent=parent,
            clear_cache=clear_cache,
            copy_children=copy_children,
            mask=mask,
            omit_list=omit_list,
            **kwargs,
        )

        if (
            cell_mask is None
            and self.cells is not None
            and new_entity.tx_id_property is None
            and self.tx_id_property is not None
            and self.tx_id_property.values is not None
        ):
            if mask is not None:
                if isinstance(self, GroundTEMReceiversLargeLoop):
                    cell_mask = mask
                else:
                    cell_mask = np.all(mask[self.cells], axis=1)
            else:
                cell_mask = np.ones(self.tx_id_property.values.shape[0], dtype=bool)

            new_entity.tx_id_property = self.tx_id_property.values[cell_mask]
        metadata["EM Dataset"][new_entity.type] = new_entity.uid
        complement: GroundTEMTransmittersLargeLoop | GroundTEMReceiversLargeLoop = (
            self.transmitters  # type: ignore
            if isinstance(self, GroundTEMReceiversLargeLoop)
            else self.receivers
        )

        if (
            new_entity.tx_id_property is not None
            and complement is not None
            and complement.tx_id_property is not None
            and complement.tx_id_property.values is not None
            and complement.vertices is not None
            and complement.cells is not None
        ):
            intersect = np.intersect1d(
                new_entity.tx_id_property.values,
                complement.tx_id_property.values,
            )

            # Convert cell indices to vertex indices
            if isinstance(complement, GroundTEMReceiversLargeLoop):
                mask = np.r_[
                    [(val in intersect) for val in complement.tx_id_property.values]
                ]
                cell_mask = None
                tx_ids = complement.tx_id_property.values[mask]
            else:
                cell_mask = np.r_[
                    [(val in intersect) for val in complement.tx_id_property.values]
                ]
                mask = np.zeros(complement.vertices.shape[0], dtype=bool)
                mask[complement.cells[cell_mask, :]] = True
                tx_ids = complement.tx_id_property.values[cell_mask]

            new_complement = super(Curve, complement).copy(  # type: ignore
                parent=parent,
                omit_list=omit_list,
                copy_children=copy_children,
                clear_cache=clear_cache,
                mask=mask,
                cell_mask=cell_mask,
            )

            if isinstance(self, GroundTEMReceiversLargeLoop):
                new_entity.transmitters = new_complement
            else:
                new_entity.receivers = new_complement

            if (
                new_complement.tx_id_property is None
                and complement.tx_id_property is not None
            ):
                new_complement.tx_id_property = tx_ids

                # Re-number the tx_id_property
                value_map = {
                    val: ind
                    for ind, val in enumerate(
                        np.r_[
                            0, np.unique(new_entity.transmitters.tx_id_property.values)
                        ]
                    )
                }
                new_map = {
                    val: new_entity.transmitters.tx_id_property.value_map.map[val]
                    for val in value_map.values()
                }
                new_complement.tx_id_property.values = np.asarray(
                    [value_map[val] for val in new_complement.tx_id_property.values]
                )
                new_entity.tx_id_property.values = np.asarray(
                    [value_map[val] for val in new_entity.tx_id_property.values]
                )
                new_entity.tx_id_property.value_map.map = new_map

        return new_entity

    @property
    def default_metadata(self) -> dict:
        """
        Default dictionary of metadata for AirborneTEM entities.
        """
        return {
            "EM Dataset": {
                "Channels": [],
                "Input type": "Tx and Rx",
                "Property groups": [],
                "Receivers": None,
                "Survey type": "Ground TEM (large-loop)",
                "Transmitters": None,
                "Tx ID property": None,
                "Unit": "Milliseconds (ms)",
                "Waveform": {"Timing mark": 0.0},
            }
        }

    @property
    def default_input_types(self) -> list[str]:
        """Choice of survey creation types."""
        return self.__INPUT_TYPE

    @property
    def default_receiver_type(self):
        """
        :return: Transmitter class
        """
        return GroundTEMReceiversLargeLoop

    @property
    def default_transmitter_type(self):
        """
        :return: Transmitter class
        """
        return GroundTEMTransmittersLargeLoop

    @property
    def tx_id_property(self) -> ReferencedData | None:
        """
        Default channel units for time or frequency defined on the child class.
        """
        if self._tx_id_property is None:
            if "Tx ID property" in self.metadata["EM Dataset"]:
                data = self.get_data(self.metadata["EM Dataset"]["Tx ID property"])

                if any(data) and isinstance(data[0], ReferencedData):
                    self._tx_id_property = data[0]

        return self._tx_id_property

    @tx_id_property.setter
    def tx_id_property(self, value: uuid.UUID | ReferencedData | np.ndarray | None):
        if isinstance(value, uuid.UUID):
            value = self.get_data(value)[0]

        if isinstance(value, np.ndarray):
            complement: GroundTEMTransmittersLargeLoop | GroundTEMReceiversLargeLoop = (
                self.transmitters  # type: ignore
                if isinstance(self, GroundTEMReceiversLargeLoop)
                else self.receivers
            )

            if complement is not None and complement.tx_id_property is not None:
                entity_type = complement.tx_id_property.entity_type
            else:
                value_map = {
                    ind: f"Loop {ind}" for ind in np.unique(value.astype(np.int32))
                }
                value_map[0] = "Unknown"
                entity_type = {  # type: ignore
                    "primitive_type": "REFERENCED",
                    "value_map": value_map,
                }

            value = self.add_data(
                {
                    "Transmitter ID": {
                        "values": value,
                        "entity_type": entity_type,
                        "type": "referenced",
                    }
                }
            )

        if not isinstance(value, (ReferencedData, type(None))):
            raise TypeError(
                "Input value for 'tx_id_property' should be of type uuid.UUID, "
                "ReferencedData, np.ndarray or None.)"
            )

        self._tx_id_property = value
        self.edit_metadata({"Tx ID property": getattr(value, "uid", None)})


class GroundTEMReceiversLargeLoop(BaseGroundTEM):  # pylint: disable=too-many-ancestors
    """
    Ground time-domain electromagnetic receivers class.
    """

    __TYPE_UID = uuid.UUID("{deebe11a-b57b-4a03-99d6-8f27b25eb2a8}")
    __TYPE = "Receivers"

    _transmitters: GroundTEMTransmittersLargeLoop | None = None

    def __init__(self, object_type: ObjectType, name="Ground TEM Rx", **kwargs):
        super().__init__(object_type, name=name, **kwargs)

    @classmethod
    def default_type_uid(cls) -> uuid.UUID:
        """
        :return: Default unique identifier
        """
        return cls.__TYPE_UID

    @property
    def default_transmitter_type(self):
        """
        :return: Transmitter class
        """
        return GroundTEMTransmittersLargeLoop

    @property
    def type(self):
        """Survey element type"""
        return self.__TYPE


class GroundTEMTransmittersLargeLoop(
    BaseGroundTEM
):  # pylint: disable=too-many-ancestors
    """
    Ground time-domain electromagnetic transmitters class.
    """

    __TYPE_UID = uuid.UUID("{17dbbfbb-3ee4-461c-9f1d-1755144aac90}")
    __TYPE = "Transmitters"

    _receivers: GroundTEMReceiversLargeLoop | None = None

    def __init__(self, object_type: ObjectType, name="Ground TEM Tx", **kwargs):
        super().__init__(object_type, name=name, **kwargs)

    @classmethod
    def default_type_uid(cls) -> uuid.UUID:
        """
        :return: Default unique identifier
        """
        return cls.__TYPE_UID

    @property
    def default_receiver_type(self):
        """
        :return: Transmitter class
        """
        return GroundTEMReceiversLargeLoop

    @property
    def type(self):
        """Survey element type"""
        return self.__TYPE
