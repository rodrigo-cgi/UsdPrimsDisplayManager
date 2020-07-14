from usd_prims_display_manager import PrimsStateLayer
from pxr import Usd, Sdf, UsdGeom
import unittest


class TestCasePrimsStateLayer(unittest.TestCase):
    def setUp(self):
        # DefineStage
        self.stage = Usd.Stage.CreateInMemory()
        self.stage.DefinePrim("/root", "Xform")

        s = UsdGeom.Xform.Define(self.stage, "/root/Sphere")
        s.AddTranslateOp().Set(value=(8, 0, 0))
        self.sr = self.stage.DefinePrim("/root/Sphere/HIGH", "Sphere")
        self.sp = self.stage.DefinePrim("/root/Sphere/PROXY", "Sphere")
        self.sr.GetAttribute("purpose").Set("render")
        self.sp.GetAttribute("purpose").Set("proxy")

        c = UsdGeom.Xform.Define(self.stage, "/root/Cone")
        c.AddTranslateOp().Set(value=(4, 0, 0))
        self.cr = self.stage.DefinePrim("/root/Cone/HIGH", "Cone")
        self.cp = self.stage.DefinePrim("/root/Cone/PROXY", "Cone")
        self.cr.GetAttribute("purpose").Set("render")
        self.cp.GetAttribute("purpose").Set("proxy")

        cl = UsdGeom.Xform.Define(self.stage, "/root/Cylinder")
        self.clr = self.stage.DefinePrim("/root/Cylinder/HIGH", "Cylinder")
        self.clr.GetAttribute("purpose").Set("render")

        self.stateLayerObj = PrimsStateLayer(self.stage)

    def test_layer(self):
        self.assertTrue(isinstance(self.stateLayerObj.layer(), Sdf.Layer))

    def test_swap_prim_purposes(self):
        primPath = Sdf.Path("/root/Sphere")
        self.stateLayerObj.swapPrimPurposes(primPath)

        self.assertFalse(self.sr.IsActive())
        self.assertEqual(self.sp.GetAttribute("purpose").Get(), "default")
        self.assertTrue(self.cr.IsActive())
        self.assertEqual(self.cp.GetAttribute("purpose").Get(), "proxy")

        primPath = Sdf.Path("/root")
        self.stateLayerObj.swapPrimPurposes(primPath)
        self.assertFalse(self.sr.IsActive())
        self.assertEqual(self.sp.GetAttribute("purpose").Get(), "default")
        self.assertFalse(self.cr.IsActive())
        self.assertEqual(self.cp.GetAttribute("purpose").Get(), "default")
        self.assertTrue(self.clr.IsActive())

    def test_set_prim_loaded(self):
        assert False

    def test_set_prim_active(self):
        assert False

    def test_set_layer_muted(self):
        assert False

    def test_save_layer_to_file(self):
        assert False

    def test_copy_spec_to_layer(self):

        destStage = Usd.Stage.CreateInMemory()
        destLayer = Sdf.Layer.CreateAnonymous()
        destStage.GetSessionLayer().subLayerPaths.append(destLayer.identifier)
        destStage.SetEditTarget(Usd.EditTarget(destLayer))
        destPrim = destStage.DefinePrim("/primsState/root", "Xform")

        primPath = Sdf.Path("/root")
        self.stateLayerObj.swapPrimPurposes(primPath)

        self.stateLayerObj.copySpecToLayer(primPath, destLayer, destPrim.GetPath())

        self.assertEqual(destStage.GetAttributeAtPath("/primsState/root/Sphere/PROXY.purpose").Get(), "default")
        self.assertEqual(destStage.GetAttributeAtPath("/primsState/root/Cone/PROXY.purpose").Get(), "default")
        self.assertFalse(destStage.GetPrimAtPath("/primsState/root/Sphere/HIGH").IsActive())
        self.assertFalse(destStage.GetPrimAtPath("/primsState/root/Cone/HIGH").IsActive())
        self.assertFalse(destStage.GetPrimAtPath("/primsState/root/Cylinder/HIGH").IsValid())



