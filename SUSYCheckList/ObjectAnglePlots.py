#!/usr/local/bin/python

from ROOT import *

from collections import OrderedDict


gROOT.LoadMacro("~/atlasstyle-00-03-04/AtlasStyle.C")
gROOT.LoadMacro("~/atlasstyle-00-03-04/AtlasLabels.C")
SetAtlasStyle()
# import style_mpl

h_var = {}

ftree = TFile("../InputNtuples/data.root")
ftree.cd()
intree = {}

intree["SR N-2"] = ftree.Get("DVTree_NTuple")

TH1.SetDefaultSumw2()

varList = []
# varList.append( ("MET","MET","(50,0,5000)")    )
# varList.append( ("MET_phi","MET #phi","(50,-3.2,3.2)")    )
varList.append( ("MET_LHT_phi","MET LHT #phi","(50,-3.2,3.2)")    )
varList.append( ("MET_L1_phi","MET L1 #phi","(50,-3.2,3.2)")    )
varList.append( ("MET_HLT_phi","MET HLT #phi","(50,-3.2,3.2)")    )
varList.append( ("MHT_HLT_phi","MHT HLT #phi","(50,-3.2,3.2)")    )
varList.append( ("MET_TST_phi","MET TST #phi","(50,-3.2,3.2)")    )
# varList.append( ("Jet_phi_leading","Leading Jet #phi","(50,-3.2,3.2)")    )
# varList.append( ("JetTrackless_phi","JetTrackless #phi","(50,-3.2,3.2)")    )

regionName = "SR N-2"

skimtree = OrderedDict()

preselectiontree = intree[regionName].Clone("preselection")
skimtree["SR N-2"] = preselectiontree.Clone("(PassCut6&&DV_passCut4)")

c = TCanvas("c","c",600,600)

colors = [1,2,3,4]


for myVar in varList:
	var,varname,bins = myVar


	legend = TLegend(0.7,0.7,0.9,0.9)

	for itree,mytree in enumerate(skimtree):
		skimtree[mytree].Draw(var+">>h%d%s"%(itree,bins), skimtree[mytree].GetName() )
		h_var[mytree] = ftree.Get("h%d"%itree).Clone("h%d"%itree)

		h_var[mytree].GetYaxis().SetTitle("Entries");
		h_var[mytree].GetXaxis().SetTitle(varname)
		h_var[mytree].SetLineColor(colors[itree])
		h_var[mytree].SetMarkerColor(colors[itree])
		h_var[mytree].SetMarkerStyle(20)
		h_var[mytree].SetMarkerSize(0.5)
		h_var[mytree].SetMinimum(0.5)
		h_var[mytree].SetMaximum(1e7)

		gPad.SetLogy()
		h_var[mytree].Draw("same e1" if itree > 0 else "e1")
		legend.AddEntry(h_var[mytree], mytree ,"LP")

	legend.SetBorderSize(1)
	legend.SetTextSize(0.03)
	legend.Draw()

	ATLASLabel(0.2,0.9,"Internal          %s"%regionName)
	c.SaveAs("%s_%s.pdf"%(var, regionName) )



