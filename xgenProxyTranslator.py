import pymel.core as pm
import mtoa.ui.ae.templates as templates
from mtoa.ui.ae.templates import AttributeTemplate, registerTranslatorUI

## we want to add this directory to the path so we can use the extra xgenArnoldUI  files
import os
import sys
localPath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(localPath)

class xgenProxyDescriptionTemplate(templates.ShapeTranslatorTemplate):
    def setup(self):
        self.commonShapeAttributes()
        self.addSeparator()
        self.addControl("aiMinPixelWidth", label="Min Pixel Width")
        self.addControl("aiMode", label= "Curve Mode")
        self.addControl("aiUseAuxRenderPatch", label = "Use Aux Render Patch")
        self.addControl("aiAuxRenderPatch", label= "Auxilary Render Patch")
        

templates.registerTranslatorUI(xgenProxyDescriptionTemplate, "xgenProxy", "xgenProxyTranslator")

