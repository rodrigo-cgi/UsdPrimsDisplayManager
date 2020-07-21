from usd_prims_display_manager import UsdPrimsDisplayManager
from pxr import Usd, Sdf, UsdGeom
import unittest
import os


class TestCaseUsdPrimsDisplayManager(unittest.TestCase):
    def setUp(self):
        # DefineStage
        self.stage = Usd.Stage.CreateInMemory()
        self.stage.DefinePrim("/root", "Xform")

        sphere = UsdGeom.Xform.Define(self.stage, "/root/Sphere")
        sphere.AddTranslateOp().Set(value=(8, 0, 0))
        self.sphereRender = self.stage.DefinePrim("/root/Sphere/HIGH", "Sphere")
        self.sphereProxy = self.stage.DefinePrim("/root/Sphere/PROXY", "Sphere")
        self.sphereRender.GetAttribute("purpose").Set("render")
        self.sphereProxy.GetAttribute("purpose").Set("proxy")

        cone = UsdGeom.Xform.Define(self.stage, "/root/Cone")
        cone.AddTranslateOp().Set(value=(4, 0, 0))
        self.coneRender = self.stage.DefinePrim("/root/Cone/HIGH", "Cone")
        self.coneProxy = self.stage.DefinePrim("/root/Cone/PROXY", "Cone")
        self.coneRender.GetAttribute("purpose").Set("render")
        self.coneProxy.GetAttribute("purpose").Set("proxy")

        cylinder = UsdGeom.Xform.Define(self.stage, "/root/Cylinder")
        self.cylinderRender = self.stage.DefinePrim("/root/Cylinder/HIGH", "Cylinder")
        self.cylinderRender.GetAttribute("purpose").Set("render")

        self.usdPrimDisplayManager = UsdPrimsDisplayManager(self.stage)

        # Add payload
        self.assetPrim = self.stage.DefinePrim("/root/Asset", "Xform")
        assetPath = "{}/data/simple_asset.usda".format(os.path.dirname(os.path.realpath(__file__)))
        self.assetPrim.GetPayloads().AddPayload(assetPath)
        self.assetRender = self.stage.GetPrimAtPath("/root/Asset/assetCube/HIGH")
        self.assetProxy = self.stage.GetPrimAtPath("/root/Asset/assetCube/PROXY")

        self.assetPrim2 = self.stage.DefinePrim("/root/Asset2", "Xform")
        assetPath = "{}/data/simple_asset.usda".format(os.path.dirname(os.path.realpath(__file__)))
        self.assetPrim2.GetPayloads().AddPayload(assetPath)
        self.asset2Render = self.stage.GetPrimAtPath("/root/Asset2/assetCube/HIGH")
        self.asset2Proxy = self.stage.GetPrimAtPath("/root/Asset2/assetCube/PROXY")

        sessLayer = self.stage.GetSessionLayer()
        self.stage.SetEditTarget(Usd.EditTarget(sessLayer))
        self.usdPrimDisplayManager.setLayerMuted(False)

    def testLayer(self):
        self.assertTrue(isinstance(self.usdPrimDisplayManager.layer, Sdf.Layer))

    def testSwapPrimPurposes(self):
        primPath = Sdf.Path("/root/Sphere")
        self.usdPrimDisplayManager.swapPrimPurposes(primPath)

        self.assertFalse(self.sphereRender.IsActive())
        self.assertEqual(self.sphereProxy.GetAttribute("purpose").Get(), "default")
        self.assertTrue(self.coneRender.IsActive())
        self.assertEqual(self.coneProxy.GetAttribute("purpose").Get(), "proxy")
        self.assertTrue(self.assetRender.IsActive())
        self.assertEqual(self.assetProxy.GetAttribute("purpose").Get(), "proxy")

        primPath = Sdf.Path("/root")
        self.usdPrimDisplayManager.swapPrimPurposes(primPath)
        self.assertFalse(self.sphereRender.IsActive())
        self.assertEqual(self.sphereProxy.GetAttribute("purpose").Get(), "default")
        self.assertFalse(self.coneRender.IsActive())
        self.assertEqual(self.coneProxy.GetAttribute("purpose").Get(), "default")
        self.assertTrue(self.cylinderRender.IsActive())
        self.assertFalse(self.assetRender.IsActive())
        self.assertEqual(self.assetProxy.GetAttribute("purpose").Get(), "default")

    def testSetPrimLoaded(self):

        self.assertTrue(self.assetPrim.IsLoaded(), True)

        self.usdPrimDisplayManager.setPrimLoaded(Sdf.Path("/root/Asset"), False)
        self.assertFalse(self.assetPrim.IsLoaded())
        self.assertFalse(self.assetPrim.GetCustomDataByKey("loaded"))

        self.usdPrimDisplayManager.setPrimLoaded(Sdf.Path("/root/Asset"), True)
        self.assertTrue(self.assetPrim.IsLoaded())
        self.assertTrue(self.assetPrim.GetCustomDataByKey("loaded"))

    def testRemoveDisplayOverrides(self):
        self.testSwapPrimPurposes()

        self.usdPrimDisplayManager.removeDisplayOverrides(Sdf.Path("/root/Sphere"))

        primPath = Sdf.Path("/root/Sphere")
        self.assertTrue(self.sphereRender.IsActive())
        self.assertEqual(self.sphereProxy.GetAttribute("purpose").Get(), "proxy")
        self.assertFalse(self.coneRender.IsActive())
        self.assertEqual(self.coneProxy.GetAttribute("purpose").Get(), "default")

    def testSetLayerMuted(self):

        tmpLayer = Sdf.Layer.CreateAnonymous()
        tmpLayer.TransferContent(self.usdPrimDisplayManager.layer)

        primPath = Sdf.Path("/root")
        self.usdPrimDisplayManager.swapPrimPurposes(primPath)
        self.usdPrimDisplayManager.setPrimLoaded(self.assetPrim2.GetPath(), False)
        self.assertFalse(self.sphereRender.IsActive())
        self.assertEqual(self.sphereProxy.GetAttribute("purpose").Get(), "default")
        self.assertFalse(self.coneRender.IsActive())
        self.assertEqual(self.coneProxy.GetAttribute("purpose").Get(), "default")
        self.assertTrue(self.cylinderRender.IsActive())
        self.assertFalse(self.assetRender.IsActive())
        self.assertEqual(self.assetProxy.GetAttribute("purpose").Get(), "default")
        self.assertFalse(self.assetPrim2.IsLoaded())

        self.stage.GetSessionLayer().subLayerPaths.remove(self.usdPrimDisplayManager.layer.identifier)
        self.assetPrim2.Load()
        self.assertNotIn(self.usdPrimDisplayManager.layer.identifier, self.stage.GetSessionLayer().subLayerPaths)

        # Tests if all the edits set with swapPrimPurposes are gone after layer was removed
        self.assertEqual(self.sphereRender.GetAttribute("purpose").Get(), "render")
        self.assertEqual(self.sphereProxy.GetAttribute("purpose").Get(), "proxy")
        self.assertEqual(self.coneRender.GetAttribute("purpose").Get(), "render")
        self.assertEqual(self.coneProxy.GetAttribute("purpose").Get(), "proxy")
        self.assertEqual(self.cylinderRender.GetAttribute("purpose").Get(), "render")
        self.assertEqual(self.assetRender.GetAttribute("purpose").Get(), "render")
        self.assertEqual(self.assetProxy.GetAttribute("purpose").Get(), "proxy")
        self.assertTrue(self.assetPrim2.IsLoaded())

        newTestedClassInstance = UsdPrimsDisplayManager(self.stage, layer=self.usdPrimDisplayManager.layer)

        newTestedClassInstance.setLayerMuted(False)

        # tests if the layer of the new instanced class is now a sublayer of the stage's session layer
        self.assertIn(newTestedClassInstance.layer.identifier, self.stage.GetSessionLayer().subLayerPaths)

        # ensures the changes made with swapPrimPurposes and Payload persists after the new instance is created
        self.assertFalse(self.sphereRender.IsActive())
        self.assertEqual(self.sphereProxy.GetAttribute("purpose").Get(), "default")
        self.assertFalse(self.coneRender.IsActive())
        self.assertEqual(self.coneProxy.GetAttribute("purpose").Get(), "default")
        self.assertTrue(self.cylinderRender.IsActive())
        self.assertFalse(self.assetRender.IsActive())
        self.assertEqual(self.assetProxy.GetAttribute("purpose").Get(), "default")
        self.assertFalse(self.assetPrim2.IsLoaded())

    def testCopySpecToLayer(self):

        destStage = Usd.Stage.CreateInMemory()
        destLayer = Sdf.Layer.CreateAnonymous()
        destStage.GetSessionLayer().subLayerPaths.append(destLayer.identifier)
        destStage.SetEditTarget(Usd.EditTarget(destLayer))
        destPrim = destStage.DefinePrim("/primsState/root", "Xform")

        primPath = Sdf.Path("/root")
        self.usdPrimDisplayManager.swapPrimPurposes(primPath)

        self.usdPrimDisplayManager.copySpecToLayer(primPath, destLayer, destPrim.GetPath())

        self.assertEqual(destStage.GetAttributeAtPath("/primsState/root/Sphere/PROXY.purpose").Get(), "default")
        self.assertEqual(destStage.GetAttributeAtPath("/primsState/root/Cone/PROXY.purpose").Get(), "default")
        self.assertFalse(destStage.GetPrimAtPath("/primsState/root/Sphere/HIGH").IsActive())
        self.assertFalse(destStage.GetPrimAtPath("/primsState/root/Cone/HIGH").IsActive())
        self.assertFalse(destStage.GetPrimAtPath("/primsState/root/Cylinder/HIGH").IsValid())
