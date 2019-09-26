import uuid

from geoh5io.shared import Coord3D

from .object_base import ObjectBase, ObjectType


class BlockModel(ObjectBase):
    __type_uid = uuid.UUID("{B020A277-90E2-4CD7-84D6-612EE3F25051}")

    def __init__(self, object_type: ObjectType, name: str, uid: uuid.UUID = None):
        super().__init__(object_type, name, uid)
        # TODO
        self._origin = Coord3D()
        self._rotation = 0
        # self._u_cell_delimiters = []
        # self._v_cell_delimiters = []
        # self._z_cell_delimiters = []

    @classmethod
    def static_type_uid(cls) -> uuid.UUID:
        return cls.__type_uid
