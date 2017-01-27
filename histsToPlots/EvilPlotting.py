#!/usr/bin/env python

import sys

import ROOT
import rootpy
from rootpy.plotting import Hist, HistStack, Legend, Canvas, Graph, Pad
from rootpy.plotting.style import get_style, set_style
from rootpy.plotting.utils import get_limits
from rootpy.io import root_open
import os, re

from rootpy import asrootpy

ROOT.gROOT.LoadMacro("AtlasStyle.C")
ROOT.gROOT.LoadMacro("AtlasLabels.C")
ROOT.SetAtlasStyle()

ROOT.gROOT.SetBatch()
rootpy.ROOT.gROOT.SetBatch()

import seaborn as sns
sns.set(style="whitegrid")


from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="inputJSONFileName", default="listOfPlots.json",
                  help="input JSON File")
parser.add_option("-o", "--output", dest="outputDir", default="plots",
                  help="output directory")
parser.add_option("-p", "--pdf",
                  action="store_true", dest="pdf", default=True,
                  help="write PDF file outputs")

(options, args) = parser.parse_args()



plotWithROOT = True
plotWithMPL = False

def getProperty(plot,key):
	if key not in plot:
		return ""
	else:
		return plot[key]


ROOT.TH1.SetDefaultSumw2()

### Let's set up the options ##################
##

import json

with open(options.inputJSONFileName) as inputJSONFile:
	input_str = inputJSONFile.read()
	input_str = re.sub(r'\\\n', '', input_str)
	input_str = re.sub(r'//.*\n', '\n', input_str)
	input_str = re.sub(",[ \t\r\n]+}", "}", input_str)
	input_str = re.sub(",[ \t\r\n]+\]", "]", input_str)
	inputJSON = json.loads(input_str)


plots = inputJSON["plots"]
# print plots

formats = []
if options.pdf:
	formats.append("pdf")

if not os.path.exists(options.outputDir):
    os.makedirs(options.outputDir)

##
###############################################

import time
timestr = time.strftime("%Y%m%d-%H%M%S")

outputRootFile = root_open(options.outputDir+"/plots_"+timestr+".root","w")

for plot in plots:
	outputRootFile.cd()
	if getProperty(plot,"aspectRatio"):
		c = Canvas(700,int(700*float(plot["aspectRatio"]) ) )
	else:
		c = Canvas(700,700)

	if getProperty(plot,"skip"):
		continue

	if getProperty(plot,"plotDim")==2:
		for hist in plot["hists"]:
			c = Canvas(700,700)
			ROOT.gPad.SetRightMargin(0.25)

			# get each hist, and draw colz. 
			tmpFile = root_open(hist[0])
			tmpHist = tmpFile.Get(str(hist[1]))

			if getProperty(plot,"lumi"):
				tmpHist.Scale(plot["lumi"])

			tmpHist.Draw("colz")

			tmpHist.GetZaxis().SetTitleOffset(1.15)

			# # set logz if requested
			ROOT.gPad.SetLogz(1 if getProperty(plot,"logZ") else 0)
			ROOT.gPad.SetGrid()

			# set titles
			tmpHist.SetTitle("{0};{1};{2};{3}".format(hist[2],*plot["titles"] ) )

			ROOT.ATLASLabel(0.2,0.9, inputJSON["ATLASLabel"]   )

			# write out the output filename with the input hist name appended
			for iformat in formats:
				c.SaveAs("%s/%s_%s.%s"%(options.outputDir,plot["plotFilename"],hist[2],iformat)  )

	elif getProperty(plot,"plotDim")==1:

		if getProperty(plot,"ratio"):
			pad1 = Pad( 0, 0.3, 1, 1.0)
			pad1.SetBottomMargin(0); # Upper and lower plot are joined
			pad1.SetGrid();          # Vertical grid
			pad1.Draw();             # Draw the upper pad: pad1
			pad2 = Pad( 0, 0.05, 1, 0.3);
			pad2.SetTopMargin(0);      # Upper and lower plot are joined
			pad2.SetBottomMargin(0.3); # Upper and lower plot are joined
			pad2.SetGrid();          # Vertical grid
			pad2.Draw();             # Draw the upper pad: pad1
			pad1.cd();               # pad1 becomes the current pad

		# Let's gather histograms

		histsToStack = []
		for ihist,hist in enumerate(getProperty(plot,"hists") ):
			tmpFile = root_open(hist[0])
			histsToStack.append( asrootpy(tmpFile.Get(str(hist[1]) )).Clone() )
			histsToStack[-1].SetTitle("{0};{1};{2};{3}".format(hist[2],*plot["titles"] ) )
			if getProperty(plot,"rebin"):
				histsToStack[-1].Rebin(plot["rebin"])
			if getProperty(plot,"xrange"):
				histsToStack[-1].GetXaxis().SetRangeUser(*plot["xrange"])


		stack = HistStack()
		if not getProperty(plot,"nostack"):
			sortedHistsToStack = sorted(histsToStack, key=lambda x: x.Integral() , reverse=False)
		else:
			sortedHistsToStack = histsToStack

		colorpal = sns.husl_palette(len(sortedHistsToStack)+1 , l=0.9, s=.4)
		darkercolorpal = sns.husl_palette(len(sortedHistsToStack)+1, l=0.4 )

		for ihist,tmphist in enumerate(sortedHistsToStack):
			if tmphist.Integral():
				if getProperty(plot,"lumi"):
					tmphist.Scale(plot["lumi"])
				if getProperty(plot,"normalize") and getProperty(plot,"nostack"):
					tmphist.Scale(1./tmphist.Integral() )

				tmphist.fillstyle = "hollow" if getProperty(plot,"nostack") else "solid"
				tmphist.fillcolor = colorpal[ihist]
				tmphist.linecolor = darkercolorpal[ihist]
				stack.Add(tmphist)


		if getProperty(plot,"normalize") and not getProperty(plot,"nostack"):
			totalIntegral = stack.sum.Integral()
			for myHist in stack:
				myHist.Scale(1./totalIntegral)

		rootstack = ROOT.THStack(stack)


		# ...and now the signal histograms

		signalHists = []
		for ihist,hist in enumerate(getProperty(plot,"signalHists")):
			tmpFile = root_open(hist[0])
			signalHists.append( asrootpy(tmpFile.Get(str(hist[1]) )).Clone()  )
			signalHists[-1].SetTitle("{0};{1};{2};{3}".format(hist[2],*plot["titles"] ) )
			if getProperty(plot,"rebin"):
				signalHists[-1].Rebin(plot["rebin"])
			if getProperty(plot,"xrange"):
				signalHists[-1].GetXaxis().SetRangeUser(*plot["xrange"])


		signalcolorpal = ["r","g","b","m","y"]

		for isignalHist, signalHist in enumerate(signalHists):
			signalHist.color = signalcolorpal[isignalHist]
			signalHist.linestyle = "dashed"
			signalHist.linewidth = 2
			if getProperty(plot,"lumi"):
				signalHist.Scale(plot["lumi"])
			if getProperty(plot,"normalize") and signalHist.Integral():
				signalHist.Scale(1./signalHist.Integral())

		# ...and now the data histograms

		dataHists = []
		for ihist,hist in enumerate(getProperty(plot,"dataHists")):
			tmpFile = root_open(hist[0])
			dataHists.append( asrootpy(tmpFile.Get(str(hist[1]) )).Clone()   )
			dataHists[-1].SetTitle("{0};{1};{2};{3}".format(hist[2],*plot["titles"] ) )
			if getProperty(plot,"rebin"):
				dataHists[-1].Rebin(plot["rebin"])
			if getProperty(plot,"xrange"):
				dataHists[-1].GetXaxis().SetRangeUser(*plot["xrange"])

		datacolorpal = ["k","r","g","b"]

		for idataHist, dataHist in enumerate(dataHists):
			dataHist.color = datacolorpal[idataHist]
			if getProperty(plot,"normalize") and dataHist.Integral():
				dataHist.Scale(1./dataHist.Integral())


		## ...finally actually going to draw everything!

		somethingDrawn = False

		drawOptions = "hist"
		drawOptions += " nostack" if getProperty(plot,"nostack") else ""
		if stack.sum.Integral():
			if somethingDrawn and "same" not in drawOptions:
				drawOptions += " same"
			rootstack.Draw(drawOptions)
			somethingDrawn = True

		drawOptions = "hist"
		for isignalHist, signalHist in enumerate(signalHists):
			if somethingDrawn and "same" not in drawOptions:
				drawOptions += " same"
			signalHist.Draw(drawOptions)
			somethingDrawn = True

		drawOptions = "e1 "
		for idataHist, dataHist in enumerate(dataHists):
			if dataHist.Integral():
				if somethingDrawn and "same" not in drawOptions:
					drawOptions += " same"
				dataHist.Draw(drawOptions)
				somethingDrawn = True

		rootstack.GetHistogram().SetTitle("{0};{1};{2};{3}".format(hist[2],*plot["titles"] ) )


		allItems = dataHists + sortedHistsToStack + signalHists

		legend = Legend( len(allItems), leftmargin=0.4, margin=0.25, topmargin=0.03, entryheight=0.025, textsize=0.03)
		for item in allItems:
			style = "L"
			if item in dataHists:
				style = "P"
			elif item in sortedHistsToStack:
				style = "F"
			legend.AddEntry(item, style=style )


		legend.SetBorderSize(1)
		legend.SetTextSize(0.03)
		legend.Draw()

		ROOT.ATLASLabel(0.2,0.9, inputJSON["ATLASLabel"]   )


		newMax = rootstack.GetMaximum()*1000. if getProperty(plot,"logY") else rootstack.GetMaximum()*1.2
		rootstack.SetMaximum(newMax)

		if getProperty(plot,"min")!="":
			rootstack.SetMinimum(plot["min"])
		if getProperty(plot,"max")!="":
			rootstack.SetMaximum(plot["max"])

		ROOT.gPad.SetLogy(1 if getProperty(plot,"logY") else 0)
		ROOT.gPad.SetGrid()

		if getProperty(plot,"ratio"):
			pad2.cd()
			for idataHist,dataHist in enumerate(dataHists):
				tmpratio = dataHist.Clone()
				tmpratio.Divide(stack.sum)
				tmpratio.Draw("e1" if idataHist==0 else "e1 same")

				tmpratio.GetYaxis().SetTitle("Ratio");
				# tmpratio.GetYaxis().SetNdivisions(505);
				tmpratio.GetYaxis().SetTitleSize(20);
				tmpratio.GetYaxis().SetTitleFont(43);
				tmpratio.GetYaxis().SetTitleOffset(1.55);
				tmpratio.GetYaxis().SetLabelFont(43); # Absolute font size in pixel (precision 3)
				tmpratio.GetYaxis().SetLabelSize(15);

				if tmpratio.GetMaximum()>10:
					tmpratio.SetMaximum(11)
				tmpratio.SetMinimum(0)

				# X axis ratio plot settings
				tmpratio.GetXaxis().SetTitleSize(18);
				tmpratio.GetXaxis().SetTitleFont(43);
				tmpratio.GetXaxis().SetTitleOffset(5.);
				tmpratio.GetXaxis().SetLabelFont(43); # Absolute font size in pixel (precision 3)
				tmpratio.GetXaxis().SetLabelSize(15)

				if getProperty(plot,"xrange"):
					tmpratio.GetXaxis().SetRangeUser(*plot["xrange"])


				unityline = ROOT.TLine()
				unityline.DrawLine(ROOT.gPad.GetUxmin(),1.,ROOT.gPad.GetUxmax(),1.)


		# write out the output filename with the input hist name appended
		for iformat in formats:
			c.SaveAs("%s/%s.%s"%(options.outputDir,plot["plotFilename"],iformat)  )
	outputRootFile.cd()
	c.Write(plot["plotFilename"])

outputRootFile.Write()
outputRootFile.Close()


