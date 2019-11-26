import os

from geoh5io.groups import ContainerGroup
from geoh5io.workspace import Workspace


def test_create_group():

    h5file = "testProject.geoh5"

    group_name = "MyTestContainer"

    # Create a workspace
    workspace = Workspace(r".\assets" + os.sep + h5file)

    group = ContainerGroup.create(workspace, name=group_name)
    group.save_to_h5()
    workspace.finalize()

    # Read the group back in
    group_object = workspace.get_entity(group_name)

    assert group_object, "Could not read the group object %s" % group_name

    os.remove(r".\assets" + os.sep + h5file)
