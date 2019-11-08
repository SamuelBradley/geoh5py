import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from geoh5io import shared


class Entity(ABC):
    def __init__(self, name: str, uid: uuid.UUID = None):
        if uid is not None:
            assert uid.int != 0
            self._uid = uid
        else:
            self._uid = uuid.uuid4()
        self._name = self.fix_up_name(name)
        self._visible = True
        self._allow_delete = True
        self._allow_rename = True
        self._public = True

    @property
    def uid(self) -> uuid.UUID:
        return self._uid

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = self.fix_up_name(new_name)

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def allow_delete(self) -> bool:
        return self._allow_delete

    @property
    def allow_rename(self) -> bool:
        return self._allow_rename

    @property
    def is_public(self) -> bool:
        return self._public

    @classmethod
    def fix_up_name(cls, name: str) -> str:
        """ If the given  name is not a valid one, transforms it to make it valid
        :return: a valid name built from the given name. It simply returns the given name
        if it was already valid.
        """
        # TODO: implement an actual fixup
        #  (possibly it has to be abstract with different implementations per Entity type)
        return name

    @property
    @abstractmethod
    def entity_type(self) -> "shared.EntityType":
        ...

    def set_parent(self, parent):
        """
        The parent of an object in the workspace
        :return: Entity: Parent entity
        """

        if isinstance(parent, uuid.UUID):
            uid = parent
        else:
            if isinstance(parent, Entity):
                uid = parent.uid
            else:
                uid = self.entity_type.workspace.get_entity("Workspace")[0].uid

        self.entity_type.workspace.tree[self.uid]["parent"] = uid

        # Add as children of parent
        if self.uid not in self.entity_type.workspace.tree[uid]["children"]:
            self.entity_type.workspace.tree[uid]["children"] += [self.uid]

    def get_parent(self):
        """
        Function to fetch the parent of an object from the workspace tree
        :return: Entity: Parent entity of object
        """

        workspace = self.entity_type.workspace
        return workspace.get_entity(workspace.tree[self.uid]["parent"])[0]

    def save_to_h5(self, close_file: bool = True):

        self.entity_type.workspace.save_entity(self, close_file=close_file)
