#!/usr/local/bin/python

from ROOT import *

from collections import OrderedDict


gROOT.LoadMacro("~/atlasstyle-00-03-04/AtlasStyle.C")
gROOT.LoadMacro("~/atlasstyle-00-03-04/AtlasLabels.C")
SetAtlasStyle()
# import style_mpl

h_den = {}
h_num = {}
h_eff = {}

ftree = TFile("../InputNtuples/data.root")
ftree.cd()
intree = {}

intree["SR N-2"] = ftree.Get("DVTree_NTuple")
# intree["CRWT"] = ftree.Get("Data_CRWT")
# intree["CRZ"] = ftree.Get("Data_CRZ")
# intree["CRY"] = ftree.Get("Data_CRY")

TH1.SetDefaultSumw2()

# var = "MuAverage"
# varname = "<#mu>"
var = "PV_n"
varname = "N_{PV}"

for regionName in intree:

	skimtree = OrderedDict()

	preselectiontree = intree[regionName].Clone("preselection")
	# skimtree["SRG3b N-2"] = preselectiontree.CopyTree("(MET>150)*( deltaQCD > 0)* ( RPT_HT5PP < 0.08  )* ( R_H2PP_H5PP > 0.2)* ( R_HT5PP_H5PP > 0.65)* ( RPZ_HT5PP < 0.6)* ( minR_pTj2i_HT3PPi > 0.08)* ( maxR_H1PPi_H2PPi < 0.98)").Clone("SRG3bN-2")
	# skimtree["SRG3b N-1"] = preselectiontree.CopyTree("(MET>150)*( deltaQCD > 0)* ( RPT_HT5PP < 0.08  )* ( R_H2PP_H5PP > 0.2)* ( R_HT5PP_H5PP > 0.65)* ( RPZ_HT5PP < 0.6)* ( minR_pTj2i_HT3PPi > 0.08)* ( maxR_H1PPi_H2PPi < 0.98)* ( H2PP > 900)").Clone("SRG3bN-1")
	# skimtree["SR N-2"] = preselectiontree.CopyTree("(MET>150)*( deltaQCD > 0)* ( RPT_HT5PP < 0.08  )* ( R_H2PP_H5PP > 0.2)* ( R_HT5PP_H5PP > 0.65)* ( RPZ_HT5PP < 0.6)* ( minR_pTj2i_HT3PPi > 0.08)* ( maxR_H1PPi_H2PPi < 0.98)* ( H2PP > 900)*(HT5PP>2800)").Clone("SRG3b")
	skimtree["SR N-2"] = preselectiontree.Clone("(PassCut6&&DV_passCut4)")

	c = TCanvas("c","c",600,600)

	colors = [1,2,3,4]


	legend = TLegend(0.7,0.7,0.9,0.9)

	preselectiontree.Draw(var+">>hden(20,0,50)")

	for itree,mytree in enumerate(skimtree):
		skimtree[mytree].Draw(var+">>h%d(20,0,50)"%itree,skimtree[mytree].GetName() )
		h_num[mytree] = ftree.Get("h%d"%itree).Clone("h%d"%itree)
		ftree.ls()
		h_den = ftree.Get("hden").Clone("hden"+mytree)

		print mytree
		print h_num[mytree].Integral()
		print h_den.Integral()

		h_eff[mytree] = h_num[mytree].Clone("heff"+mytree)
		h_eff[mytree].Reset()

		h_eff[mytree].Divide(h_num[mytree],h_den,1,1,"B")
		h_eff[mytree].GetYaxis().SetTitle("Efficiency wrt Preselection");
		h_eff[mytree].GetXaxis().SetTitle(varname)
		h_eff[mytree].SetLineColor(colors[itree])
		h_eff[mytree].SetMarkerColor(colors[itree])
		h_eff[mytree].SetMarkerStyle(20)
		h_eff[mytree].SetMarkerSize(0.5)
		h_eff[mytree].SetMinimum(1e-3)
		h_eff[mytree].SetMaximum(2)

		gPad.SetLogy()
		h_eff[mytree].Draw("same e1" if itree > 0 else "e1")
		legend.AddEntry(h_eff[mytree], mytree ,"LP")


	legend.SetBorderSize(1)
	legend.SetTextSize(0.03)
	legend.Draw()

	ATLASLabel(0.2,0.9,"Internal          %s"%regionName)
	c.SaveAs("AcceptanceVs%s_%s.pdf"%(var, regionName) )

	

# c = TCanvas("c","c",1400,300)
# h_den.SetMarkerStyle(20)
# h_den.SetMarkerSize(0.5)

# h_den.Draw()

# ATLASLabel(0.2,0.9,"Internal ")
# c.SaveAs("LumiVsRun.pdf")







