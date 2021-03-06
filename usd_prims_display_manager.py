from pxr import Sdf, Usd, Vt
from enum import Enum


def iteratePrimChildren(prim):
    for _prim in prim.GetChildren():
        for i in iteratePrimChildren(_prim):
            yield _prim
    yield prim

 
def iteratePrimSpecs(parentPrims):
    """Utility function to create a generator with all prim specs child to the given prim specs

    To iterate the whole Sdf.Layer you can pass the rootPrimsSpecs to this function

    Args:
        parentPrims (set[`Sdf.PrimSpec`]):
            A set of prim specs to iterate

    Yields:
        `Sdf.PrimSpec`:

    """
    for parentPrim in parentPrims:
        for primSpec in parentPrim.nameChildren:
            for each in iteratePrimSpecs({primSpec, }):
                yield each
        yield parentPrim


class UsdPrimsDisplayManager(object):

    drawModeAttribute = "model:drawMode"
    purposeAttribute = "purpose"

    def __init__(self, stage, layer=None, proxyPrimPrefix="", renderPrimPrefix=""):
        """Manages the display status of Prims, serializing and manipulating the prim's display state

        This class manages the following properties/attributes
        - Payload's loading state
        - Prim's Activation
        - Purposes swap
        - Bounding Box / Geo display

        Note that the class is initialised with the Display overrides muted.
        Use UsdPrimsDisplayManager.setMuted(True) to activate

        Args:
            stage (`Usd.Stage`):
                The stage object of the current scene
            layer (`Sdf.Layer`):
                A layer generated by this class.
            layer (str):
                Overloaded attribute that accepts a file path instead of a Sdf. Object
            proxyPrimPrefix (str):
                in case the proxy purpose prims have a default naming convention. It's recommended to use this attribute
                since it improves the traverse's speed
            renderPrimPrefix (str):
                in case the render purpose prims have a default naming convention. It's recommended to use this attribute
                since it improves the traverse's speed

        """

        self._stage = stage

        # Layer
        if layer is None:
            self._layer = Sdf.Layer.CreateAnonymous()
        elif isinstance(layer, Sdf.Layer):
            self._layer = layer
        elif isinstance(layer, str):
            self._layer = Sdf.Layer.Open(layer)

        self._layer.SetMuted(True)
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

    class DrawMode(Enum):
        inherit = 0
        geometry = 1
        boundingBox = 2

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
            if childPrim.GetAttribute(self.purposeAttribute).Get() == "render":
                renderPrim = childPrim
            elif childPrim.GetAttribute(self.purposeAttribute).Get() == "proxy":
                proxyPrim = childPrim

        # Todo: add filter name
        if renderPrim is None or proxyPrim is None:
            # continue finding prims.
            for childPrim in children:
                self.swapPrimPurposes(childPrim.GetPath())
            return

        with self.editInPrimStateLayer():
            renderPrim.SetActive(False)
            proxyPrim.GetAttribute(self.purposeAttribute).Set("default")

    def setPrimActive(self, primPath, state):
        """Sets the active state of the prim

        Args:
            primPath (`Sdf.Path`):
                The Sdf Path of the prim to change
            state (bool):
                True to activate the Prim,

        """

        prim = self._stage.GetPrimAtPath(primPath)
        with self.editInPrimStateLayer():
            prim.SetActive(state)

    def setPrimLoaded(self, primPath, state):
        """Sets the loading state of prim's payload

        Args:
            state (bool):
                True for loaded prim

        Returns:
            bool:
                True if the prim at primPath was changed.

        """
        prim = self._stage.GetPrimAtPath(primPath)
        if not prim.IsValid() or not prim.HasPayload():
            return False

        if not state and prim.IsLoaded():
            prim.Unload()
        if state and not prim.IsLoaded():
            prim.Load()

        with self.editInPrimStateLayer():
            prim.SetCustomDataByKey("loaded", state)
        return True

    def setPrimDrawMode(self, primPath, drawMode):
        """Sets prim draw mode, Bounding Box or Full Geo

        Args:
            drawMode (`UsdPrimsDisplayManager.DrawMode`):
                draw mode defined in self.DrawMode enum
        """
        prim = self._stage.GetPrimAtPath(primPath)
        if not primPath.IsValid():
            return False

        if drawMode == self.DrawMode.inherit:
            prim.RemoveProperty(self.drawModeAttribute)
            return True
        if drawMode == self.DrawMode.geometry:
            prim.GetAttribute(self.drawModeAttribute).Clear()
            return True
        if drawMode == self.DrawMode.boundingBox:
            prim.GetAttribute(self.drawModeAttribute).Set(Vt.Token("bounds"))
            return True

        return False

    def removeDisplayOverrides(self, primPath):
        """Cleans the opinions on the Display's manager layer, restoring prim to underneath layer's state

        Args:
            primPath (`Sdf.Path`):
                The path to remove edit

        """
        with self.editInPrimStateLayer():
            self._stage.RemovePrim(primPath)

    def setLayerMuted(self, state):
        """set the Muted state of the layer

        Args:
            state (bool):
                True to mute the layer

        """

        # Stores how the stage was loaded, either with loaded or unloaded prims
        # Usually defined when opening the Stage with the "loaded" argument
        # This functionality depends on the  all the Load/Unload in the client to be done with this class
        initialLoadSet = False  # Unloaded == False
        for loadablePrimPath in self._stage.FindLoadable():
            loadablePrim = self._stage.GetPrimAtPath(loadablePrimPath)
            if loadablePrim.HasPayload() and not loadablePrim.GetCustomDataByKey("loaded"):
                initialLoadSet = loadablePrim.IsLoaded()
                break
        self._layer.SetMuted(state)

        # Load prims
        for primSpec in iteratePrimSpecs(self._layer.rootPrims.values()):
            storedLoadState = primSpec.customData.get("loaded")
            if storedLoadState is None:
                continue
            prim = self._stage.GetPrimAtPath(primSpec.path)
            if not state:  # Layer not muted
                if storedLoadState and not prim.IsLoaded():
                    prim.Load()
                if not storedLoadState and prim.IsLoaded():
                    prim.Unload()

            else:  # Layer muted
                if initialLoadSet and not prim.IsLoaded():
                    prim.Load()
                elif not initialLoadSet and prim.IsLoaded():
                    prim.Unload()

    def saveLayerToFile(self, filePath):
        """writes the layer to a file in disk

        Args:
            filePath (str):
                str with a valid filepath
        """
        outputLayer = Sdf.Layer.CreateNew(filePath)
        outputLayer.TransferContent(self._layer)
        outputLayer.Save()

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
