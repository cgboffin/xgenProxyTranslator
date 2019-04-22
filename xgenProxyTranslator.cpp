#define DLLEXPORT

#include <extension/Extension.h>
#include <session/SessionOptions.h>
#include <session/ArnoldSession.h>
#include <scene/MayaScene.h>
#include <utils/time.h>

#include <maya/MFileObject.h>

#include "xgenProxyTranslator.h"

#include <string>


#ifdef _WIN32
#define PATH_SEPARATOR "\\"
#else
#define PATH_SEPARATOR "/"
#endif

#define DEBUG_MTOA

using namespace std;

extern "C"
{

	DLLEXPORT void initializeExtension(CExtension& extension)
	{
		MStatus status;
		extension.Requires("xgenProxy");
		status = extension.RegisterTranslator("xgenProxy",
			"",
			CXgProxyDescriptionTranslator::creator, CXgProxyDescriptionTranslator::NodeInitializer);
	}

	DLLEXPORT void deinitializeExtension(CExtension& extension)
	{
	}

}

AtNode* CXgProxyDescriptionTranslator::CreateArnoldNodes()
{
	AiMsgInfo("[CXgProxyDescriptionTranslator] CreateArnoldNodes()");
	return AddArnoldNode("procedural");
}

void CXgProxyDescriptionTranslator::Export(AtNode* instance)
{
	AiMsgInfo("[CXgProxyDescriptionTranslator] Exporting %s", GetMayaNodeName().asChar());
	Update(instance);
}

const double *CXgProxyDescriptionTranslator::GetMotionFramesExpanded(unsigned int &count)
{
	const std::vector<double> &motionFrames = CMayaScene::GetArnoldSession()->GetMotionFrames();
	count = motionFrames.size();
	return (count == 0) ? NULL : &motionFrames[0];
}

struct DescInfo
{
	std::string strScene;
	std::string xgenFilePath;
	std::string alembicFilePath;
	std::string strPalette;
	std::string strDescription;
	std::string strPatch;
	int strDebug;
	int strWarning;
	int strInfo;
	std::vector<std::string> vecPatches;
	float fFrame;
	uint  renderMode;
	uint  moblur;  //
	uint  moblurmode;  // Position (Center On Frame)
	uint  motionBlurSteps;  // Step (Keys) 3
	float moblurFactor;  // Length (Frames) (0.5)
	float aiMotionFrames;  // Length (0.5)
	float aiMotionStart;  // Start End (0.25, -0.25)
	float aiMotionEnd;  // Start End (0.25, -0.25)
	int aiMotionSteps;  // Length (Keys/Step) (0.5)

	bool  hasAlembicFile;

	float aiMinPixelWidth;
	int aiMode; // ribbon or tube

	bool  bCameraOrtho;
	float fCameraPos[3];
	float fCameraFOV;
	float fCameraInvMat[16];
	float fCamRatio;
	float fBoundingBox[6];

	std::string auxRenderPatch;
	bool useAuxRenderPatch;

	void setBoundingBox(float xmin, float ymin, float zmin, float xmax, float ymax, float zmax)
	{
		fBoundingBox[0] = xmin;
		fBoundingBox[1] = ymin;
		fBoundingBox[2] = zmin;

		fBoundingBox[3] = xmax;
		fBoundingBox[4] = ymax;
		fBoundingBox[5] = zmax;
	}

	void setCameraPos(float x, float y, float z)
	{
		fCameraPos[0] = x;
		fCameraPos[1] = y;
		fCameraPos[2] = z;
	}

	void setCameraInvMat(float m00, float m01, float m02, float m03,
		float m10, float m11, float m12, float m13,
		float m20, float m21, float m22, float m23,
		float m30, float m31, float m32, float m33)
	{
		fCameraInvMat[0] = m00;
		fCameraInvMat[1] = m01;
		fCameraInvMat[2] = m02;
		fCameraInvMat[3] = m03;
		fCameraInvMat[4] = m10;
		fCameraInvMat[5] = m11;
		fCameraInvMat[6] = m12;
		fCameraInvMat[7] = m13;
		fCameraInvMat[8] = m20;
		fCameraInvMat[9] = m21;
		fCameraInvMat[10] = m22;
		fCameraInvMat[11] = m23;
		fCameraInvMat[12] = m30;
		fCameraInvMat[13] = m31;
		fCameraInvMat[14] = m32;
		fCameraInvMat[15] = m33;
	}
};

void CXgProxyDescriptionTranslator::Update(AtNode* procedural)
{
	AiMsgInfo("[CXgProxyDescriptionTranslator] Update()");
	// Build the path to the procedural dso
#ifdef _WIN32
	static string strDSO = string(getenv("MTOA_PATH")) + string("/procedurals/xgen_procedural.dll");
#else 
	static string strDSO = string(getenv("MTOA_PATH")) + string("/procedurals/xgen_procedural.so");
#endif
	
	std::string strUnitConvMat;
	float fUnitConvFactor = 1.f;
	{
		std::string strCurrentUnits;
		{
			MString mstrCurrentUnits;
			MGlobal::executeCommand("currentUnit -q -linear", mstrCurrentUnits);
			strCurrentUnits = mstrCurrentUnits.asChar();
		}

		static std::map<std::string, std::pair<std::string, float> > s_mapUnitsConv;
		if (s_mapUnitsConv.empty())
		{
			s_mapUnitsConv["in"] = std::pair<std::string, float>("2.54", 2.54f);
			s_mapUnitsConv["ft"] = std::pair<std::string, float>("30.48", 30.48f);
			s_mapUnitsConv["yd"] = std::pair<std::string, float>("91.44", 91.44f);
			s_mapUnitsConv["mi"] = std::pair<std::string, float>("160934.4", 160934.4f);
			s_mapUnitsConv["mm"] = std::pair<std::string, float>("0.1", 0.1f);
			s_mapUnitsConv["km"] = std::pair<std::string, float>("100000.0", 100000.f);
			s_mapUnitsConv["m"] = std::pair<std::string, float>("100.0", 100.f);
			s_mapUnitsConv["dm"] = std::pair<std::string, float>("10.0", 10.f);
		}

		std::string factor = "1";
		std::map<std::string, std::pair<std::string, float> >::const_iterator it = s_mapUnitsConv.find(strCurrentUnits);
		if (it != s_mapUnitsConv.end())
		{
			factor = it->second.first;
			fUnitConvFactor = it->second.second;
		}
		strUnitConvMat = " -world " + factor + ";0;0;0;0;" + factor + ";0;0;0;0;" + factor + ";0;0;0;0;1";
	}

	// Extract description info from the current maya shape node.
	DescInfo info;
	{
		// The Description node being exported
		MFnDagNode  xgenDesc;
		xgenDesc.setObject(m_dagPath.node());

		// The render options of the scene
		MObject m_renderOptions = GetArnoldRenderOptions();
		MFnDependencyNode renderOptions;
		renderOptions.setObject(m_renderOptions);

		// Hardcoded values for now.
		float s = 10000.f * fUnitConvFactor;
		info.setBoundingBox(-s, -s, -s, s, s, s);
		info.bCameraOrtho = false;
		info.fCamRatio = 1.0;
		info.fFrame = (float)MAnimControl::currentTime().value();

		// Get Description and Palette from the dag paths.
		// The current dag path points to the desciption.
		// We get the parent to get the palette name.
		info.xgenFilePath = xgenDesc.findPlug("xgenFilePath").asString().asChar();
		info.strPalette = xgenDesc.findPlug("palette").asString().asChar();
		info.alembicFilePath = xgenDesc.findPlug("alembicFilePath").asString().asChar();
		info.strPatch = xgenDesc.findPlug("patch").asString().asChar();
		info.strDescription = xgenDesc.findPlug("description").asString().asChar();
		info.strDebug = xgenDesc.findPlug("xgenDebugLogLevel").asInt();
		info.strWarning = xgenDesc.findPlug("xgenWarningLogLevel").asInt();
		info.strInfo = xgenDesc.findPlug("xgenInfoLogLevel").asInt();

		info.renderMode = xgenDesc.findPlug("renderMode").asInt();
		info.aiMinPixelWidth = xgenDesc.findPlug("aiMinPixelWidth").asFloat();
		info.aiMode = xgenDesc.findPlug("aiMode").asInt();
		info.moblur = xgenDesc.findPlug("motionBlurOverride").asInt();
		info.moblurmode = xgenDesc.findPlug("motionBlurMode").asInt();
		info.motionBlurSteps = 1;
		info.moblurFactor = 0.5;
		info.auxRenderPatch = xgenDesc.findPlug("aiAuxRenderPatch").asString().asChar();
		info.useAuxRenderPatch = xgenDesc.findPlug("aiUseAuxRenderPatch").asBool();

		//  use render globals moblur settings
		bool motionBlurEnabled = renderOptions.findPlug("motion_blur_enable").asBool();
		if (info.moblur == 0)
		{
			if (motionBlurEnabled)
			{
				/*info.motionBlurSteps = renderOptions.findPlug("motion_steps").asInt();
				info.moblurFactor = xgenDesc.findPlug("motion_frames").asFloat();*/
				CXgProxyDescriptionTranslator::GetMotionFramesExpanded(info.motionBlurSteps);
				info.moblurFactor = (float)GetMotionByFrame();
			}
		}
		// use  xgen per  description moblur settings
		else if (info.moblur == 1)
		{
			info.motionBlurSteps = xgenDesc.findPlug("motionBlurSteps").asInt();
			info.moblurFactor = xgenDesc.findPlug("motionBlurFactor").asFloat();
		}

		// culling Camera setup
		MPlug cullingCameraPlug = xgenDesc.findPlug("cullingCamera");
		MDagPath camera;
		MPlugArray connections;
		cullingCameraPlug.connectedTo(connections, true, false);
		if (connections.length() > 0)
		{
			MDagPath::getAPathTo(connections[0].node(), camera);
		}
		if (camera.isValid() && camera.hasFn(MFn::kCamera))
		{
			MStatus status;
			AiMsgInfo("[CXgProxyDescriptionTranslator] camera: %s", camera.fullPathName().asChar());

			// info.setCameraPos
			MMatrix tm = camera.inclusiveMatrix(&status);
			info.setCameraPos((float)tm[3][0], (float)tm[3][1], (float)tm[3][2]);
			AiMsgDebug("inclusiveMatrix: %f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f",
				(float)tm[0][0], (float)tm[1][0], (float)tm[2][0], (float)tm[0][3],
				(float)tm[0][1], (float)tm[1][1], (float)tm[2][1], (float)tm[1][3],
				(float)tm[0][2], (float)tm[1][2], (float)tm[2][2], (float)tm[2][3],
				(float)tm[3][0], (float)tm[3][1], (float)tm[3][2], (float)tm[3][3]);

			// info.setCameraInvMat
			// This is correct. Maya expects a mix of the inverted and not inverted matrix
			//  values, and also with translation values in a different place.
			MMatrix tmi = camera.inclusiveMatrixInverse(&status);
			info.setCameraInvMat((float)tm[0][0], (float)tm[1][0], (float)tm[2][0], (float)tm[0][3],
				(float)tm[0][1], (float)tm[1][1], (float)tm[2][1], (float)tm[1][3],
				(float)tm[0][2], (float)tm[1][2], (float)tm[2][2], (float)tm[2][3],
				(float)tmi[3][0], (float)tmi[3][1], (float)tmi[3][2], (float)tm[3][3]);
			AiMsgDebug("inclusiveMatrixInverse: %f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f",
				(float)tm[0][0], (float)tm[1][0], (float)tm[2][0], (float)tm[0][3],
				(float)tm[0][1], (float)tm[1][1], (float)tm[2][1], (float)tm[1][3],
				(float)tm[0][2], (float)tm[1][2], (float)tm[2][2], (float)tm[2][3],
				(float)tmi[3][0], (float)tmi[3][1], (float)tmi[3][2], (float)tm[3][3]);

			MFnCamera fnCamera(camera);
			// info.fCameraFOV
			info.fCameraFOV = (float)fnCamera.horizontalFieldOfView(&status) * AI_RTOD;
			info.bCameraOrtho = false;
			// info.fCamRatio
			info.fCamRatio = (float)fnCamera.aspectRatio(&status);
		}
	}

	char buf[512];
	string mbSamplesString;

	// motion blur
	if (info.moblur != 2 && info.motionBlurSteps > 1 && info.moblurFactor > 0.0f)
	{
		if (info.moblur == 0) // use render globals
		{
			AiNodeDeclare(procedural, "time_samples", "constant ARRAY FLOAT");
			AtArray* samples = AiArrayAllocate(info.motionBlurSteps, 1, AI_TYPE_FLOAT);

			unsigned int motionFramesCount;
			const double *steps = CXgProxyDescriptionTranslator::GetMotionFramesExpanded(motionFramesCount);
			if (steps != NULL && motionFramesCount > 0)
			{

				for (uint sampCount = 0; sampCount < info.motionBlurSteps; sampCount++)
				{
					float sample = float(steps[sampCount] - GetExportFrame());

					// If 0.0 used as start step. XGen will not refresh next mb changes until frame is changed
					if (sampCount == 0 && sample == 0.0f)
						sample = 0.0001f;

					sprintf(buf, "%f", sample);
					mbSamplesString += std::string(buf) + " ";

					AiArraySetFlt(samples, sampCount, sample);
				}
				AiNodeSetArray(procedural, "time_samples", samples);
			}
		}
		else // xgen blur on
		{
			MFloatArray steps;
			float stepSize = info.moblurFactor / (info.motionBlurSteps - 1);

			AiNodeDeclare(procedural, "time_samples", "constant ARRAY FLOAT");
			AtArray* samples = AiArrayAllocate(info.motionBlurSteps, 1, AI_TYPE_FLOAT);

			for (uint stepCount = 0; stepCount < info.motionBlurSteps; stepCount++)
			{
				if (info.moblurmode == 0)
					steps.append(float(0.0001 + (stepSize*stepCount))); // If 0.0 used as start step. XGen will not refresh next mb changes
				else if (info.moblurmode == 1)
					steps.append(float((0.0 - (info.moblurFactor / 2.0)) + (stepSize*stepCount)));
				else
					steps.append(float((0.0 - info.moblurFactor) + (stepSize*stepCount)));
			}

			for (uint sampCount = 0; sampCount < info.motionBlurSteps; sampCount++)
			{
				float sample = steps[sampCount];

				sprintf(buf, "%f", sample);
				mbSamplesString += std::string(buf) + " ";

				AiArraySetFlt(samples, sampCount, sample);
			}
			AiNodeSetArray(procedural, "time_samples", samples);
		}
	}
	else
	{
		mbSamplesString += std::string("0.0");
	}

	AtNode* rootShader = NULL;
	// Create a nested procedural node
	AtNode* shape;
	shape = procedural;

	//ExportMatrix(shape, info.motionBlurSteps);

	AiNodeSetStr(shape, "name", NodeUniqueName(shape, buf));
	ProcessRenderFlags(shape);

	// Export shaders
	rootShader = ExportShaders(shape);
	AiNodeDeclare(shape, "xgen_shader", "constant ARRAY NODE");
	AiNodeSetArray(shape, "xgen_shader", AiArray(1, 1, AI_TYPE_NODE, rootShader));
	// Set the procedural arguments
	{
		std::string strData;
		sprintf(buf, "%d", info.strDebug);
		strData += "-debug " + std::string(buf);
		sprintf(buf, "%d", info.strWarning);
		strData += " -warning " + std::string(buf);
		sprintf(buf, "%d", info.strInfo);
		strData += " -stats " + std::string(buf);
		sprintf(buf, "%f ", GetExportFrame());
		strData += " -frame " + std::string(buf);
		strData += " -file " + info.xgenFilePath;
		strData += " -palette " + info.strPalette;
		strData += " -geom " + info.alembicFilePath;
		strData += " -patch " + info.strPatch;
		strData += " -description " + info.strDescription;

		MTime oneSec(1.0, MTime::kSeconds);
		float fps = (float)oneSec.asUnits(MTime::uiUnit());
		sprintf(buf, "%f ", fps);
		strData += " -fps " + std::string(buf);

		strData += " -motionSamplesLookup " + mbSamplesString;
		strData += " -motionSamplesPlacement " + mbSamplesString;

		strData += strUnitConvMat;

		// Set other arguments
		AiNodeSetBool(shape, "load_at_init", true);
		AiNodeSetStr(shape, "dso", strDSO.c_str());
		AiNodeSetStr(shape, "data", strData.c_str());
		AiNodeSetPnt(shape, "min", info.fBoundingBox[0], info.fBoundingBox[1], info.fBoundingBox[2]);
		AiNodeSetPnt(shape, "max", info.fBoundingBox[3], info.fBoundingBox[4], info.fBoundingBox[5]);

		AiNodeDeclare(shape, "irRenderCam", "constant STRING");
		AiNodeDeclare(shape, "irRenderCamFOV", "constant STRING");
		AiNodeDeclare(shape, "irRenderCamXform", "constant STRING");
		AiNodeDeclare(shape, "irRenderCamRatio", "constant STRING");

		sprintf(buf, "%s,%f,%f,%f", info.bCameraOrtho ? "true" : "false", info.fCameraPos[0], info.fCameraPos[1], info.fCameraPos[2]);
		AiNodeSetStr(shape, "irRenderCam", buf);

		sprintf(buf, "%f", info.fCameraFOV);
		AiNodeSetStr(shape, "irRenderCamFOV", buf);

		sprintf(buf, "%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f",
			info.fCameraInvMat[0], info.fCameraInvMat[1], info.fCameraInvMat[2], info.fCameraInvMat[3],
			info.fCameraInvMat[4], info.fCameraInvMat[5], info.fCameraInvMat[6], info.fCameraInvMat[7],
			info.fCameraInvMat[8], info.fCameraInvMat[9], info.fCameraInvMat[10], info.fCameraInvMat[11],
			info.fCameraInvMat[12], info.fCameraInvMat[13], info.fCameraInvMat[14], info.fCameraInvMat[15]);
		AiNodeSetStr(shape, "irRenderCamXform", buf);

		sprintf(buf, "%f", info.fCamRatio);
		AiNodeSetStr(shape, "irRenderCamRatio", buf);
		AiNodeDeclare(shape, "xgen_renderMethod", "constant STRING");
		sprintf(buf, "%i", info.renderMode);
		AiNodeSetStr(shape, "xgen_renderMethod", buf);

		AiNodeDeclare(shape, "ai_mode", "constant INT");
		AiNodeSetInt(shape, "ai_mode", info.aiMode);

		AiNodeDeclare(shape, "ai_min_pixel_width", "constant FLOAT");
		AiNodeSetFlt(shape, "ai_min_pixel_width", info.aiMinPixelWidth);
	}

}

void CXgProxyDescriptionTranslator::ExportMotion(AtNode* shape, unsigned int step)
{
	// Check if motionblur is enabled and early out if it's not.
	if (!IsMotionBlurEnabled()) return;

	// Set transform matrix
	ExportMatrix(shape, step);
}

void CXgProxyDescriptionTranslator::NodeInitializer(CAbTranslator context)
{
	CExtensionAttrHelper helper(context.maya, "procedural");
	CShapeTranslator::MakeCommonAttributes(helper);
	CShapeTranslator::MakeMayaVisibilityFlags(helper);
	CAttrData data;

	// render mode  1 = live  3 = batch
	data.defaultValue.INT = 1;
	data.name = "renderMode";
	data.shortName = "render_mode";
	helper.MakeInputInt(data);

	data.defaultValue.INT = 0;
	data.name = "motionBlurOverride";
	data.shortName = "motion_blur_override";
	helper.MakeInputInt(data);

	MStringArray  enumNames;
	enumNames.append("Start On Frame");
	enumNames.append("Center On Frame");
	enumNames.append("End On Frame");
	enumNames.append("Use RenderGlobals");
	data.defaultValue.INT = 3;
	data.name = "motionBlurMode";
	data.shortName = "motion_blur_mode";
	data.enums = enumNames;
	helper.MakeInputEnum(data);

	data.defaultValue.INT = 3;
	data.name = "motionBlurSteps";
	data.shortName = "motion_blur_steps";
	helper.MakeInputInt(data);

	data.defaultValue.FLT = 0.5;
	data.name = "motionBlurFactor";
	data.shortName = "motion_blur_factor";
	helper.MakeInputFloat(data);

	data.defaultValue.FLT = 1.0;
	data.name = "motionBlurMult";
	data.shortName = "motion_blur_mult";
	helper.MakeInputFloat(data);

	data.defaultValue.FLT = 0.15;
	data.name = "aiMinPixelWidth";
	data.shortName = "ai_min_pixel_width";
	helper.MakeInputFloat(data);

	MStringArray  curveTypeEnum;
	curveTypeEnum.append("Ribbon");
	curveTypeEnum.append("Thick");
	data.defaultValue.INT = 0;
	data.name = "aiMode";
	data.shortName = "ai_mode";
	data.enums = curveTypeEnum;
	helper.MakeInputEnum(data);

	data.defaultValue.BOOL = false;
	data.name = "aiUseAuxRenderPatch";
	data.shortName = "ai_use_aux_render_patch";
	helper.MakeInputBoolean(data);

	data.defaultValue.STR = "";
	data.name = "aiAuxRenderPatch";
	data.shortName = "ai_batch_render_patch";
	helper.MakeInputString(data);
}

AtNode* CXgProxyDescriptionTranslator::ExportShaders(AtNode* instance)
{
	MPlug shadingGroupPlug = GetNodeShadingGroup(m_dagPath.node(), 0);
	if (!shadingGroupPlug.isNull())
	{
		AtNode *rootShader = ExportNode(shadingGroupPlug);
		if (rootShader != NULL)
		{
			AiNodeSetPtr(instance, "shader", rootShader);
			return rootShader;
		}
	}

	return NULL;
}


