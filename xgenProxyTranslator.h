// Copyright 2013 Autodesk, Inc. All rights reserved. 
//
// Use of this software is subject to the terms of the Autodesk 
// license agreement provided at the time of installation or download, 
// or which otherwise accompanies this software in either electronic 
// or hard copy form.

#ifndef __XGENMTOAEXTENSION_H__
#define __XGENMTOAEXTENSION_H__

#include <translators/shape/ShapeTranslator.h>

class CXgProxyDescriptionTranslator : public CShapeTranslator
{
public:

	AtNode* CreateArnoldNodes();
	virtual void Export(AtNode* shape);
	virtual void Update(AtNode* shape);
	void ExportMotion(AtNode*, unsigned int);
	const double *GetMotionFramesExpanded(unsigned int &count);

	static void* creator()
	{
		return new CXgProxyDescriptionTranslator();
	}
	static void NodeInitializer(CAbTranslator context);
private:

	AtNode* ExportShaders(AtNode* instance); protected:
};

#endif

