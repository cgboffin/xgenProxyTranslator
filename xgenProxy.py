###############################################################################
##
## xgenProxy.py
##
## Description:
##    Registers a new type of shape with maya called "xgenProxy".
##    This shape will display rectangles, triangles, and circles using basic gl
##
##
##    There are no output attributes for this shape.
##    The following input attributes define the type of shape to draw.
##
##       shapeType  : 0=rectangle, 1=circle, 2=triangle
##       radius		: circle radius
##       height		: rectangle and triangle height
##		 width		: rectangle and triangle width
##
################################################################################

# Usage:
# import maya
# maya.cmds.loadPlugin("xgenProxy.py")
# maya.cmds.createNode("xgenProxy")
#
# An object will be created with reference to the node.  By default it will be a rectangle.
# Use the different options node options to change the type of shape or its size and shape.
# Add textures or manipulate as with any other object.
#

import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaRender as OpenMayaRender
import maya.OpenMayaUI as OpenMayaUI

import math
import sys

kPluginNodeTypeName = "xgenProxy"
xgenProxyId = OpenMaya.MTypeId(0x8671309)

glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
glFT = glRenderer.glFunctionTable()

kLeadColor = 18  # green
kActiveColor = 15  # white
kActiveAffectedColor = 8  # purple
kDormantColor = 4  # blue
kHiliteColor = 17  # pale blue

kDefaultRadius = 1.0
kDefaultHeight = 2.0
kDefaultWidth = 2.0
kDefaultShapeType = 0


class basicGeom:
    radius = kDefaultRadius
    height = kDefaultHeight
    width = kDefaultWidth
    shapeType = kDefaultShapeType


class xgenProxy(OpenMayaMPx.MPxSurfaceShape):
    def __init__(self):
        OpenMayaMPx.MPxSurfaceShape.__init__(self)

        # class variables
        aShapeType = OpenMaya.MObject()
        aRadius = OpenMaya.MObject()
        aHeight = OpenMaya.MObject()
        aWidth = OpenMaya.MObject()

        time = OpenMaya.MObject()
        xgenFilePath = OpenMaya.MObject()
        alembicFilePath = OpenMaya.MObject()
        palette = OpenMaya.MObject()
        description = OpenMaya.MObject()
        patch = OpenMaya.MObject()
        cullingCamera = OpenMaya.MObject()
        xgenDebugLogLevel = OpenMaya.MObject()
        xgenWarningLogLevel = OpenMaya.MObject()
        xgenStatsLogLevel = OpenMaya.MObject()

        # geometry
        self.__myGeometry = basicGeom()

    # override
    def postConstructor(self):
        """
         When instances of this node are created internally, the MObject associated
         with the instance is not created until after the constructor of this class
         is called. This means that no member functions of MPxSurfaceShape can
         be called in the constructor.
         The postConstructor solves this problem. Maya will call this function
         after the internal object has been created.
         As a general rule do all of your initialization in the postConstructor.
        """
        self.setRenderable(True)

    # override
    def compute(self, plug, dataBlock):
        """
         Since there are no output attributes this is not necessary but
         if we wanted to compute an output mesh for rendering it would
         be done here base on the inputs.
        """
        if plug == xgenProxy.time:
            dataHandle = dataBlock.inputValue(xgenProxy.xgenFilePath)
            xgenString = dataHandle.asString()
            outputHandle = dataBlock.outputValue(xgenProxy.xgenFilePath)
            outputHandle.setString(xgenString)

            dataHandle = dataBlock.inputValue(xgenProxy.alembicFilePath)
            xgenString = dataHandle.asString()
            outputHandle = dataBlock.outputValue(xgenProxy.alembicFilePath)
            outputHandle.setString(xgenString)

            dataHandle = dataBlock.inputValue(xgenProxy.palette)
            xgenString = dataHandle.asString()
            outputHandle = dataBlock.outputValue(xgenProxy.palette)
            outputHandle.setString(xgenString)

            dataHandle = dataBlock.inputValue(xgenProxy.description)
            xgenString = dataHandle.asString()
            outputHandle = dataBlock.outputValue(xgenProxy.description)
            outputHandle.setString(xgenString)

            dataHandle = dataBlock.inputValue(xgenProxy.patch)
            xgenString = dataHandle.asString()
            outputHandle = dataBlock.outputValue(xgenProxy.patch)
            outputHandle.setString(xgenString)

            dataBlock.setClean(plug)
        else:
            return OpenMaya.kUnknownParameter

    # override
    def getInternalValue(self, plug, datahandle):
        """
         Handle internal attributes.
         In order to impose limits on our attribute values we
         mark them internal and use the values in fGeometry intead.
        """
        if (plug == xgenProxy.aRadius):
            datahandle.setDouble(self.__myGeometry.radius)

        elif (plug == xgenProxy.aHeight):
            datahandle.setDouble(self.__myGeometry.height)

        elif (plug == xgenProxy.aWidth):
            datahandle.setDouble(self.__myGeometry.width)

        else:
            return OpenMayaMPx.MPxSurfaceShape.getInternalValue(self, plug, datahandle)

        return True

    # override
    def setInternalValue(self, plug, datahandle):
        """
         Handle internal attributes.
         In order to impose limits on our attribute values we
         mark them internal and use the values in fGeometry intead.
        """

        # the minimum radius is 0
        #
        if (plug == xgenProxy.aRadius):
            radius = datahandle.asDouble()

            if (radius < 0):
                radius = 0

            self.__myGeometry.radius = radius

        elif (plug == xgenProxy.aHeight):
            val = datahandle.asDouble()
            if (val <= 0):
                val = 0.1
            self.__myGeometry.height = val

        elif (plug == xgenProxy.aWidth):
            val = datahandle.asDouble()
            if (val <= 0):
                val = 0.1
            self.__myGeometry.width = val

        else:
            return OpenMayaMPx.MPxSurfaceShape.setInternalValue(self, plug, datahandle)

        return True

    # override
    def isBounded(self):
        return True

    # override
    def boundingBox(self):
        """
         Returns the bounding box for the shape.
         In this case just use the radius and height attributes
         to determine the bounding box.
        """
        result = OpenMaya.MBoundingBox()

        geom = self.geometry()

        r = geom.radius
        result.expand(OpenMaya.MPoint(r, r, r))
        result.expand(OpenMaya.MPoint(-r, -r, -r))

        r = geom.height / 2.0
        result.expand(OpenMaya.MPoint(r, r, r))
        result.expand(OpenMaya.MPoint(-r, -r, -r))

        r = geom.width / 2.0
        result.expand(OpenMaya.MPoint(r, r, r))
        result.expand(OpenMaya.MPoint(-r, -r, -r))

        return result

    def geometry(self):
        """
         This function gets the values of all the attributes and
         assigns them to the fGeometry. Calling MPlug::getValue
         will ensure that the values are up-to-date.
        """
        # return self.__myGeometry

        this_object = self.thisMObject()

        plug = OpenMaya.MPlug(this_object, xgenProxy.aRadius)
        self.__myGeometry.radius = plug.asDouble()

        plug.setAttribute(xgenProxy.aHeight)
        self.__myGeometry.height = plug.asDouble()

        plug.setAttribute(xgenProxy.aWidth)
        self.__myGeometry.width = plug.asDouble()

        plug.setAttribute(xgenProxy.aShapeType)
        self.__myGeometry.shapeType = plug.asShort()  # enum????

        return self.__myGeometry


def printMsg(msg):
    print msg
    stream = OpenMaya.MStreamUtils.stdOutStream()
    OpenMaya.MStreamUtils.writeCharBuffer(stream, msg)


class xgenProxyUI(OpenMayaMPx.MPxSurfaceShapeUI):
    # private enums
    __kDrawRectangle, __kDrawCircle, __kDrawTriangle = range(3)
    __kDrawWireframe, __kDrawWireframeOnShaded, __kDrawSmoothShaded, __kDrawFlatShaded, __kLastToken = range(5)

    def __init__(self):
        OpenMayaMPx.MPxSurfaceShapeUI.__init__(self)

    # override
    def getDrawRequests(self, info, objectAndActiveOnly, queue):
        """
         The draw data is used to pass geometry through the
         draw queue. The data should hold all the information
         needed to draw the shape.
        """
        data = OpenMayaUI.MDrawData()
        # printMsg("**before getProtoype\n");
        request = info.getPrototype(self)
        # printMsg("**after getProtoype\n");
        shapeNode = self.surfaceShape()
        geom = shapeNode.geometry()
        self.getDrawData(geom, data)
        request.setDrawData(data)

        # Are we displaying meshes?
        if (not info.objectDisplayStatus(OpenMayaUI.M3dView.kDisplayMeshes)):
            return

        # Use display status to determine what color to draw the object
        if (info.displayStyle() == OpenMayaUI.M3dView.kWireFrame):
            self.getDrawRequestsWireframe(request, info)
            queue.add(request)

        elif (info.displayStyle() == OpenMayaUI.M3dView.kGouraudShaded):
            request.setToken(xgenProxyUI.__kDrawSmoothShaded)
            self.getDrawRequestsShaded(request, info, queue, data)
            queue.add(request)

        elif (info.displayStyle() == OpenMayaUI.M3dView.kFlatShaded):
            request.setToken(xgenProxyUI.__kDrawFlatShaded)
            self.getDrawRequestsShaded(request, info, queue, data)
            queue.add(request)
        return

    # override
    def draw(self, request, view):
        """
         From the given draw request, get the draw data and determine
         which basic to draw and with what values.
        """
        data = request.drawData()
        shapeNode = self.surfaceShape()
        geom = shapeNode.geometry()
        token = request.token()
        drawTexture = False

        # set up texturing if it is shaded
        if ((token == xgenProxyUI.__kDrawSmoothShaded) or
                (token == xgenProxyUI.__kDrawFlatShaded)):
            # Set up the material
            material = request.material()
            material.setMaterial(request.multiPath(), request.isTransparent())

            # Enable texturing
            #
            # Note, Maya does not enable texturing when drawing with the
            # default material. However, your custom shape is free to ignore
            # this setting.
            #
            drawTexture = material.materialIsTextured() and not view.usingDefaultMaterial()

            # Apply the texture to the current view
            if (drawTexture):
                material.applyTexture(view, data)

        glFT.glPushAttrib(OpenMayaRender.MGL_ALL_ATTRIB_BITS)

        if ((token == xgenProxyUI.__kDrawSmoothShaded) or
                (token == xgenProxyUI.__kDrawFlatShaded)):
            glFT.glEnable(OpenMayaRender.MGL_POLYGON_OFFSET_FILL)
            glFT.glPolygonMode(OpenMayaRender.MGL_FRONT_AND_BACK, OpenMayaRender.MGL_FILL)
            if (drawTexture):
                glFT.glEnable(OpenMayaRender.MGL_TEXTURE_2D)
        else:
            glFT.glPolygonMode(OpenMayaRender.MGL_FRONT_AND_BACK, OpenMayaRender.MGL_LINE)

        # draw the shapes
        if (geom.shapeType == xgenProxyUI.__kDrawCircle):
            # circle
            glFT.glBegin(OpenMayaRender.MGL_POLYGON)
            for i in range(0, 360):
                rad = (i * 2 * math.pi) / 360;
                glFT.glNormal3f(0.0, 0.0, 1.0)
                if (i == 360):
                    glFT.glTexCoord3f(geom.radius * math.cos(0), geom.radius * math.sin(0), 0.0)
                    glFT.glVertex3f(geom.radius * math.cos(0), geom.radius * math.sin(0), 0.0)
                else:
                    glFT.glTexCoord3f(geom.radius * math.cos(rad), geom.radius * math.sin(rad), 0.0)
                    glFT.glVertex3f(geom.radius * math.cos(rad), geom.radius * math.sin(rad), 0.0)
            glFT.glEnd()

        elif (geom.shapeType == xgenProxyUI.__kDrawRectangle):
            # rectangle
            glFT.glBegin(OpenMayaRender.MGL_QUADS)

            glFT.glTexCoord2f(-1 * (geom.width / 2), -1 * (geom.height / 2))
            glFT.glVertex3f(-1 * (geom.width / 2), -1 * (geom.height / 2), 0.0)
            glFT.glNormal3f(0, 0, 1.0)

            glFT.glTexCoord2f(-1 * (geom.width / 2), (geom.height / 2))
            glFT.glVertex3f(-1 * (geom.width / 2), (geom.height / 2), 0.0)
            glFT.glNormal3f(0, 0, 1.0)

            glFT.glTexCoord2f((geom.width / 2), (geom.height / 2))
            glFT.glVertex3f((geom.width / 2), (geom.height / 2), 0.0)
            glFT.glNormal3f(0, 0, 1.0)

            glFT.glTexCoord2f((geom.width / 2), -1 * (geom.height / 2))
            glFT.glVertex3f((geom.width / 2), -1 * (geom.height / 2), 0.0)
            glFT.glNormal3f(0, 0, 1.0)
            glFT.glEnd()

        else:
            # triangle
            glFT.glBegin(OpenMayaRender.MGL_TRIANGLES)
            glFT.glTexCoord2f(-1 * (geom.width / 2), -1 * (geom.height / 2))
            glFT.glVertex3f(-1 * (geom.width / 2), -1 * (geom.height / 2), 0.0)
            glFT.glNormal3f(0.0, 0.0, 1.0)

            glFT.glTexCoord2f(0.0, (geom.height / 2))
            glFT.glVertex3f(0.0, (geom.height / 2), 0.0)
            glFT.glNormal3f(0.0, 0.0, 1.0)

            glFT.glTexCoord2f((geom.width / 2), -1 * (geom.height / 2))
            glFT.glVertex3f((geom.width / 2), -1 * (geom.height / 2), 0.0)
            glFT.glNormal3f(0.0, 0.0, 1.0)
            glFT.glEnd()

        if ((token == xgenProxyUI.__kDrawSmoothShaded) or
                (token == xgenProxyUI.__kDrawFlatShaded)):
            glFT.glDisable(OpenMayaRender.MGL_POLYGON_OFFSET_FILL)
            # Turn off texture mode
            if (drawTexture):
                glFT.glDisable(OpenMayaRender.MGL_TEXTURE_2D)

        glFT.glPopAttrib()

    def select(self, selectInfo, selectionList, worldSpaceSelectPts):
        """
         Select function. Gets called when the bbox for the object is selected.
         This function just selects the object without doing any intersection tests.
        """

        priorityMask = OpenMaya.MSelectionMask(OpenMaya.MSelectionMask.kSelectObjectsMask)
        item = OpenMaya.MSelectionList()
        item.add(selectInfo.selectPath())
        xformedPt = OpenMaya.MPoint()
        selectInfo.addSelection(item, xformedPt, selectionList,
                                worldSpaceSelectPts, priorityMask, False)
        return True

    def getDrawRequestsWireframe(self, request, info):

        request.setToken(xgenProxyUI.__kDrawWireframe)

        displayStatus = info.displayStatus()
        activeColorTable = OpenMayaUI.M3dView.kActiveColors
        dormantColorTable = OpenMayaUI.M3dView.kDormantColors

        if (displayStatus == OpenMayaUI.M3dView.kLead):
            request.setColor(kLeadColor, activeColorTable)

        elif (displayStatus == OpenMayaUI.M3dView.kActive):
            request.setColor(kActiveColor, activeColorTable)

        elif (displayStatus == OpenMayaUI.M3dView.kActiveAffected):
            request.setColor(kActiveAffectedColor, activeColorTable)

        elif (displayStatus == OpenMayaUI.M3dView.kDormant):
            request.setColor(kDormantColor, dormantColorTable)

        elif (displayStatus == OpenMayaUI.M3dView.kHilite):
            request.setColor(kHiliteColor, activeColorTable)

    def getDrawRequestsShaded(self, request, info, queue, data):
        # Need to get the material info
        path = info.multiPath()  # path to your dag object
        view = info.view()  # view to draw to
        material = OpenMayaMPx.MPxSurfaceShapeUI.material(self, path)
        usingDefaultMat = view.usingDefaultMaterial()
        if usingDefaultMat:
            material = OpenMayaUI.MMaterial.defaultMaterial()

        displayStatus = info.displayStatus()

        # Evaluate the material and if necessary, the texture.
        try:
            material.evaluateMaterial(view, path)
        except RuntimeError:
            print "Couldn't evaluate material"
            raise

        drawTexture = not usingDefaultMat
        if (drawTexture and material.materialIsTextured()):
            material.evaluateTexture(data)

        request.setMaterial(material)

        # create a draw request for wireframe on shaded if necessary.
        if ((displayStatus == OpenMayaUI.M3dView.kActive) or
                (displayStatus == OpenMayaUI.M3dView.kLead) or
                (displayStatus == OpenMayaUI.M3dView.kHilite)):
            wireRequest = info.getPrototype(self)
            wireRequest.setDrawData(data)
            self.getDrawRequestsWireframe(wireRequest, info)
            wireRequest.setToken(xgenProxyUI.__kDrawWireframeOnShaded)
            wireRequest.setDisplayStyle(OpenMayaUI.M3dView.kWireFrame)
            queue.add(wireRequest)


def nodeCreator():
    return OpenMayaMPx.asMPxPtr(xgenProxy())


def uiCreator():
    return OpenMayaMPx.asMPxPtr(xgenProxyUI())


def nodeInitializer():
    # BASIC type enumerated attribute
    enumAttr = OpenMaya.MFnEnumAttribute()
    xgenProxy.aShapeType = enumAttr.create("shapeType", "st", kDefaultShapeType)
    enumAttr.addField("rectangle", 0)
    enumAttr.addField("circle", 1)
    enumAttr.addField("triangle", 2)
    enumAttr.setHidden(False)
    enumAttr.setKeyable(True)
    xgenProxy.addAttribute(xgenProxy.aShapeType)

    # BASIC numeric attributes
    # utility func for numeric attrs
    def setOptions(attr):
        attr.setHidden(False)
        attr.setKeyable(True)
        attr.setInternal(True)

    numericAttr = OpenMaya.MFnNumericAttribute()

    xgenProxy.aRadius = numericAttr.create("radius", "r", OpenMaya.MFnNumericData.kDouble, kDefaultRadius)
    setOptions(numericAttr)
    xgenProxy.addAttribute(xgenProxy.aRadius)

    xgenProxy.aHeight = numericAttr.create("height", "ht", OpenMaya.MFnNumericData.kDouble, kDefaultHeight)
    setOptions(numericAttr)
    xgenProxy.addAttribute(xgenProxy.aHeight)

    xgenProxy.aWidth = numericAttr.create("width2", "wt2", OpenMaya.MFnNumericData.kDouble, kDefaultWidth)
    setOptions(numericAttr)
    xgenProxy.addAttribute(xgenProxy.aWidth)

    xgenProxy.xgenDebugLogLevel = numericAttr.create("xgenDebugLogLevel", "xgdl", OpenMaya.MFnNumericData.kInt, 1)
    setOptions(numericAttr)
    xgenProxy.addAttribute(xgenProxy.xgenDebugLogLevel)

    xgenProxy.xgenWarningLogLevel = numericAttr.create("xgenWarningLogLevel", "xgwl", OpenMaya.MFnNumericData.kInt, 1)
    setOptions(numericAttr)
    xgenProxy.addAttribute(xgenProxy.xgenWarningLogLevel)

    xgenProxy.xgenInfoLogLevel = numericAttr.create("xgenInfoLogLevel", "xgil", OpenMaya.MFnNumericData.kInt, 1)
    setOptions(numericAttr)
    xgenProxy.addAttribute(xgenProxy.xgenInfoLogLevel)

    def setOptions(attr):
        attr.setHidden(False)
        attr.setKeyable(False)

    messageAttr = OpenMaya.MFnMessageAttribute()
    xgenProxy.cullingCamera = messageAttr.create("cullingCamera", "culcam")
    setOptions(messageAttr)
    xgenProxy.addAttribute(xgenProxy.cullingCamera)

    def setOptions(attr):
        attr.setHidden(False)
        attr.setKeyable(False)
        attr.setWritable(True)
        attr.setStorable(True)

    unitAttr = OpenMaya.MFnUnitAttribute()
    xgenProxy.time = unitAttr.create("time", "tm", OpenMaya.MFnUnitAttribute.kTime, 0.0)
    xgenProxy.addAttribute(xgenProxy.time)

    kDefaultXgenFilePathAttrValue = ''
    xgenFilePathData = OpenMaya.MFnStringData().create(kDefaultXgenFilePathAttrValue)
    stringAttr = OpenMaya.MFnTypedAttribute()
    xgenProxy.xgenFilePath = stringAttr.create("xgenFilePath", "xp", OpenMaya.MFnData.kString, xgenFilePathData)
    stringAttr.setUsedAsFilename(True)
    setOptions(stringAttr)
    xgenProxy.addAttribute(xgenProxy.xgenFilePath)

    kDefaultAlembicFilePathAttrValue = ''
    alembicFilePathData = OpenMaya.MFnStringData().create(kDefaultAlembicFilePathAttrValue)
    xgenProxy.alembicFilePath = stringAttr.create("alembicFilePath", "ap", OpenMaya.MFnData.kString,
                                                  alembicFilePathData)
    stringAttr.setUsedAsFilename(True)
    setOptions(stringAttr)
    xgenProxy.addAttribute(xgenProxy.alembicFilePath)

    kDefaultPaletteAttrValue = ''
    paletteData = OpenMaya.MFnStringData().create(kDefaultPaletteAttrValue)
    xgenProxy.palette = stringAttr.create("palette", "plt", OpenMaya.MFnData.kString, paletteData)
    xgenProxy.addAttribute(xgenProxy.palette)

    kDefaultDescriptionAttrValue = ''
    descriptionData = OpenMaya.MFnStringData().create(kDefaultDescriptionAttrValue)
    xgenProxy.description = stringAttr.create("description", "dsc", OpenMaya.MFnData.kString, descriptionData)
    setOptions(stringAttr)
    xgenProxy.addAttribute(xgenProxy.description)

    kDefaultpatchAttrValue = ''
    patchData = OpenMaya.MFnStringData().create(kDefaultpatchAttrValue)
    xgenProxy.patch = stringAttr.create("patch", "ptch", OpenMaya.MFnData.kString, patchData)
    setOptions(stringAttr)
    xgenProxy.addAttribute(xgenProxy.patch)

    xgenProxy.attributeAffects(xgenProxy.time, xgenProxy.xgenFilePath)
    xgenProxy.attributeAffects(xgenProxy.time, xgenProxy.alembicFilePath)
    xgenProxy.attributeAffects(xgenProxy.time, xgenProxy.palette)
    xgenProxy.attributeAffects(xgenProxy.time, xgenProxy.description)
    xgenProxy.attributeAffects(xgenProxy.time, xgenProxy.patch)


# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "Autodesk", "2017", "Any")
    try:
        mplugin.registerShape(kPluginNodeTypeName, xgenProxyId,
                              nodeCreator, nodeInitializer, uiCreator)
    except:
        sys.stderr.write("Failed to register node: %s" % kPluginNodeTypeName)
        raise


# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(xgenProxyId)
    except:
        sys.stderr.write("Failed to deregister node: %s" % kPluginNodeTypeName)
        raise
