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

text = ROOT.TLatex()

# outputRootFile = root_open(options.outputDir+"/plots_"+timestr+".root","w")

for plot in plots:
	# outputRootFile.cd()
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

			if "*" in hist[0]:
				if not os.path.isfile("%s.root"%hist[0].split("*")[0] ):
					os.system("hadd -f %s.root %s"%(hist[0].split("*")[0], hist[0] ) )
				tmpFile = root_open( "%s.root"%hist[0].split("*")[0]  )
			else:
				tmpFile = root_open(hist[0])

			tmpHist = asrootpy(tmpFile.Get(str(hist[1])).Clone())

			if len(hist)>3:
				tmpHist.Scale( eval(hist[3]) )

			if getProperty(plot,"lumi"):
				tmpHist.Scale(plot["lumi"])

			tmpHist.Draw("colz2")
			if not getProperty(plot,"noProfile"):
				tmpHist.ProfileX().Draw("same")


			datacolorpal = ["k","r","g","b"]



			if getProperty(plot,"dataHists"):
				for idataHist,dataHist in enumerate(plot["dataHists"]):
					# get each hist, and draw colz. 
					tmpDataFile = root_open(dataHist[0])
					tmpDataHist = asrootpy(tmpDataFile.Get(str(dataHist[1])).Clone("dataHist%d"%idataHist))
					tmpDataHist.color = datacolorpal[idataHist]
					tmpDataHist.Draw("same text")



			tmpHist.GetZaxis().SetTitleOffset(1.15)

			if getProperty(plot,"xRange"):
				tmpHist.GetXaxis().SetRangeUser(*plot["xRange"])
			if getProperty(plot,"yRange"):
				tmpHist.GetYaxis().SetRangeUser(*plot["yRange"])

			if getProperty(plot,"min")!="":
				tmpHist.SetMinimum(plot["min"])
			if getProperty(plot,"max")!="":
				tmpHist.SetMaximum(plot["max"])

			# # # set log if requested
			ROOT.gPad.SetLogx(1 if getProperty(plot,"logX") else 0)
			ROOT.gPad.SetLogy(1 if getProperty(plot,"logY") else 0)
			ROOT.gPad.SetLogz(1 if getProperty(plot,"logZ") else 0)
			ROOT.gPad.SetGrid()

			tmpHist.GetXaxis().SetMoreLogLabels(1 if getProperty(plot,"logX") else 0)
			tmpHist.GetYaxis().SetMoreLogLabels(1 if getProperty(plot,"logY") else 0)

			# set titles
			tmpHist.SetTitle("{0};{1};{2};{3}".format(hist[2],*plot["titles"] ) )

			if getProperty(plot,"box"):
				box = ROOT.TBox()
				box.SetFillStyle(0)
				box.SetLineStyle(7)
				box.DrawBox(*plot["box"])
				if getProperty(plot,"boxIntegral"):
					#calculate integral in box
					tmpError = ROOT.Double()
					tmpIntegral = tmpHist.IntegralAndError(
						tmpHist.GetXaxis().FindBin(plot["box"][0]),
						tmpHist.GetXaxis().FindBin(plot["box"][2]),
						tmpHist.GetYaxis().FindBin(plot["box"][1]),
						tmpHist.GetYaxis().FindBin(plot["box"][3]),
						tmpError
						)
					# print tmpIntegral, tmpError
					#print it in the box
					text.SetNDC(0)
					text.SetTextSize(0.015)
					text.DrawLatex(plot["box"][0]*1.1,plot["box"][1]*1.1,"Integral in region: %.02f #pm %.02f"%(tmpIntegral,tmpError) )

			if getProperty(plot,"xdiv"):
				tmpHist.SetNdivisions(int(plot["xdiv"]),"x")
			if getProperty(plot,"ydiv"):
				tmpHist.SetNdivisions(int(plot["ydiv"]),"y")

			ROOT.ATLASLabel(0.4,0.9, inputJSON["ATLASLabel"]   )
			text.SetNDC()
			text.SetTextSize(0.02)
			text.DrawLatex(0.17,0.97,hist[2])
			if getProperty(plot,"lumi"):
				text.SetTextSize(0.025)
				text.DrawLatex(0.4,0.87,"Data 2016, L = %s fb^{-1}"%plot["lumi"])


			# write out the output filename with the input hist name appended
			for iformat in formats:
				c.SaveAs("%s/%s_%s.%s"%(options.outputDir,plot["plotFilename"],str(hist[2]).translate(None," #{}()_,^=."),iformat)  )

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

			if "*" in hist[0]:
				if not os.path.isfile("%s.root"%hist[0].split("*")[0] ):
					os.system("hadd -f %s.root %s"%(hist[0].split("*")[0], hist[0] ) )
				tmpFile = root_open( "%s.root"%hist[0].split("*")[0]  )
			else:
				tmpFile = root_open(hist[0])
			histsToStack.append( asrootpy(tmpFile.Get(str(hist[1]) )).Clone() )
			histsToStack[-1].SetTitle("{0};{1};{2};{3}".format(hist[2],*plot["titles"] ) )
			if getProperty(plot,"rebin"):
				histsToStack[-1].Rebin(plot["rebin"])
			if getProperty(plot,"xrange"):
				histsToStack[-1].GetXaxis().SetRangeUser(*plot["xrange"])
			if len(hist)>3:
				histsToStack[-1].Scale( eval(hist[3]) )



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
					startBin = 0 if not getProperty(plot,"normalizeFrom") else tmphist.FindBin(plot["normalizeFrom"])
					tmphist.Scale(1./tmphist.Integral(startBin,-1) )

				tmphist.fillstyle = "hollow" if getProperty(plot,"nostack") else "solid"
				tmphist.fillcolor = colorpal[ihist]
				tmphist.linecolor = darkercolorpal[ihist]
				tmphist.linewidth = 2
				stack.Add(tmphist)


		if getProperty(plot,"normalize") and not getProperty(plot,"nostack"):
			startBin = 0 if not getProperty(plot,"normalizeFrom") else stack.sum.FindBin(plot["normalizeFrom"])
			totalIntegral = stack.sum.Integral(startBin,-1)
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
				startBin = 0 if not getProperty(plot,"normalizeFrom") else signalHist.FindBin(plot["normalizeFrom"])
				signalHist.Scale(1./signalHist.Integral(startBin,-1  ))

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
				startBin = 0 if not getProperty(plot,"normalizeFrom") else dataHist.FindBin(plot["normalizeFrom"])
				dataHist.Scale(1./dataHist.Integral(startBin,-1))


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


		if getProperty(plot,"integralAbove"):
			if stack.sum.Integral():
				print "stack has integral above %f of %f"%(plot["integralAbove"], stack.sum.Integral( stack.sum.FindBin(plot["integralAbove"]) ,-1) )
			for idataHist, dataHist in enumerate(dataHists):
				if dataHist.Integral():
					print "data has integral above %f of %f"%(plot["integralAbove"], dataHist.Integral( dataHist.FindBin(plot["integralAbove"]) ,-1) )

		if getProperty(plot,"fit"):
			for idataHist, dataHist in enumerate(dataHists):
				fitFunc = rootpy.R.TF1("fit",plot["fit"][0], float(plot["fit"][1]), float(plot["fit"][2]) )
				dataHist.Fit(fitFunc,"R")
				dataHist.Reset()
				fitFunc.SetLineColor(ROOT.kRed)
				fitFunc.SetLineWidth(2)
				fitFunc.Clone().Draw("same")
				fitFunc.SetLineWidth(1)
				fitFunc.SetLineStyle(2)
				fitFunc.SetRange(dataHist.GetXaxis().GetXmin(),dataHist.GetXaxis().GetXmax() )
				fitFunc.Clone().Draw("same")
				if getProperty(plot,"integralAbove"):
					print "fit has integral %f"%fitFunc.Integral( plot["integralAbove"], 1e9 )

		rootstack.GetHistogram().SetTitle("{0};{1};{2};{3}".format(hist[2],*plot["titles"] ) )


		newMax = rootstack.GetMaximum()*1000. if getProperty(plot,"logY") else rootstack.GetMaximum()*1.2
		rootstack.SetMaximum(newMax)

		if getProperty(plot,"min")!="":
			rootstack.SetMinimum(plot["min"])
		if getProperty(plot,"max")!="":
			rootstack.SetMaximum(plot["max"])

		ROOT.gPad.SetLogy(1 if getProperty(plot,"logY") else 0)
		ROOT.gPad.SetGrid()


		allItems = dataHists + sortedHistsToStack + signalHists

		legend = Legend( len(allItems), leftmargin=0.1, margin=0.25, topmargin=0.06, entryheight=0.02)

		for item in allItems:
			style = "L"
			if item in dataHists:
				if getProperty(plot,"fit"):
					continue
				style = "P"
			elif item in sortedHistsToStack:
				style = "F"
			legend.AddEntry(item, style=style )


		legend.SetBorderSize(1)
		legend.SetTextSize(0.025)
		legend.SetLineWidth(0)
		legend.Draw()

		ROOT.ATLASLabel(0.2,0.9, inputJSON["ATLASLabel"]   )


		if getProperty(plot,"verticalLines"):
			verticalLine = ROOT.TLine()
			verticalLine.SetLineWidth(2)
			verticalLine.SetLineStyle(5)
			for vertLineValue in plot["verticalLines"]:
				verticalLine.DrawLine(vertLineValue, ROOT.gPad.GetUymin(), vertLineValue, ROOT.gPad.GetUymax())


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
	# outputRootFile.cd()
	# c.Write(plot["plotFilename"])

# outputRootFile.Write()
# outputRootFile.Close()


