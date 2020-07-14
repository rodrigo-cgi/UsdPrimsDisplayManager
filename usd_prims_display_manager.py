from pxr import Sdf, Usd


class UsdPrimsDisplayManager(object):

    def __init__(self, stage, proxyPrimPrefix="", renderPrimPrefix=""):
        self._stage = stage
        self._layer = Sdf.Layer.CreateAnonymous()
        self._stage.GetSessionLayer().subLayerPaths.append(self._layer.identifier)
        self._proxyPrimPrefix = proxyPrimPrefix
        self._renderPrimPrefix = renderPrimPrefix

    class __EditInLayer(object):
        """Context manager that ensures the Stage edits are happening in the PrimStateLayer """
        def __init__(self, primStateLayer):
            """
            Args:
                primStateLayer (`PrimsStateLayer`):
                    Instance of the enclosing parent class

            """
            self._primStateLayer = primStateLayer
            self.editTarget = self._primStateLayer.stage.GetEditTarget()

        def __enter__(self):
            self._primStateLayer.stage.SetEditTarget(Usd.EditTarget(self._primStateLayer.layer))

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._primStateLayer.stage.SetEditTarget(self.editTarget)

    def editInPrimStateLayer(self):
        """Context utility to edit the stage in the Prim State Layer. to be called using `with` statement"""
        return self.__EditInLayer(self)

    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, stage):
        """Changes the current stage of the class. Will cause a reset of the class

        Args:
            stage (`Usd.Stage`):
                Initialised valid stage to replace the current class stage
        """
        self._stage = stage
        self._layer = Sdf.Layer.CreateAnonymous()
        self._stage.GetSessionLayer().subLayerPaths.append(self._layer.identifier)

    @property
    def layer(self):
        return self._layer

    def swapPrimPurposes(self, primPath):
        """Either add or remove the prim at the given path from the swapped purpose layer

        Args:
            primPath (`Sdf.Path`):
                the path of the prim to have all their children swapped.

        """
        if not primPath.IsPrimPath():
            return

        prim = self._stage.GetPrimAtPath(primPath)
        children = prim.GetChildren()
        renderPrim = proxyPrim = None
        for childPrim in children:
            if childPrim.GetAttribute("purpose").Get() == "render":
                renderPrim = childPrim
            elif childPrim.GetAttribute("purpose").Get() == "proxy":
                proxyPrim = childPrim

        # Todo: add filter name
        if renderPrim is None or proxyPrim is None:
            # continue finding prims.
            for childPrim in children:
                self.swapPrimPurposes(childPrim.GetPath())
            return

        with self.editInPrimStateLayer():
            renderPrim.SetActive(False)
            proxyPrim.GetAttribute("purpose").Set("default")

    def setPrimLoaded(self, primPath, state):
        """Either add or remove the prim at the given path from the swapped purpose layer

        Args:
            primPath (`Sdf.Path`):
                the path of the prim to have all their children swapped.

        """
        # TODO
        prim = self._stage.GetPrimAtPath(primPath)

    def setPrimActive(self, primPath, state):
        """Either add or remove the prim at the given path from the swapped purpose layer

        Args:
            primPath (`Sdf.Path`):
                the path of the prim to have all their children swapped.

        """
        prim = self._stage.GetPrimAtPath(primPath)

    def setLayerMuted(self, state):
        """Swaps the muting state of the layer

        Args:
            state (bool):
                If layer should be muted or not

        """
        # TODO
        self._layer.SetMuted(state)

    def saveLayerToFile(self, filePath):
        """writes the layer to a file in disk

        Args:
            filePath (str):
                str with a valid filepath
        """

        self._layer

    def copySpecToLayer(self, primPath, layer, destPrimPath):
        """Copies the specs of primPath and all children to a prim in another layer

        Args:
            primPath (`Sdf.Path`):
                The path of the prims to copy
            destPrimPath (`Sdf.Path`):
                The destination path on the destination layer
            layer  (`Sdf.Layer`):
                destination layer

        """
        Sdf.CopySpec(self._layer, primPath, layer, destPrimPath)
