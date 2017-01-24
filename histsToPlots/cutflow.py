#!/usr/bin/env python

import ROOT
import numpy as np
from rootpy.plotting import Hist, HistStack, Legend, Canvas, Graph
from rootpy.plotting.style import get_style, set_style
from rootpy.plotting.utils import get_limits
from rootpy.interactive import wait
from rootpy.io import root_open
import rootpy.plotting.root2matplotlib as rplt
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from pylab import *
import os

from ATLASStyle import *

# import style_mpl

import seaborn as sns
sns.set(style="whitegrid")

from matplotlib import rc
rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
rc('text', usetex=True)

mpl.rcParams['text.latex.preamble'] = [
       r'\usepackage{siunitx}',   # i need upright \micro symbols, but you need...
       r'\sisetup{detect-all}',   # ...this to force siunitx to actually use your fonts
       r'\usepackage{helvet}',    # set the normal font here
       r'\usepackage{sansmath}',  # load up the sansmath so that math -> helvet
       r'\sansmath'               # <- tricky! -- gotta actually tell tex to use!
]  


makeCutFlowTables = True
if makeCutFlowTables:
	import cutFlowTools

samples = [
			# 'Data',
			'QCD',
			'Top',
			'W',
			'Z',
			'Diboson',
			]


lumiscale = 3.24

colorpal = sns.color_palette("husl", 4 )



colors = {
	'Data': 'black',
	'QCD': 'gray',
	'Top': colorpal[0],
	'W': colorpal[1],
	'Z': colorpal[2],
	'Diboson': colorpal[3],
}

# colors = {
# 	'Data': 'black',
# 	'QCD': 'gray',
# 	'Top': 'red',
# 	'W': 'green',
# 	'Z': 'blue',
# }


myfiles = {
	# 'Data':   'hists/hist-DataMain_periodC.root.root',
	'QCD':    'hists/output/QCD/hist-QCD.root.root',
	'Top':    'hists/output/Top/hist-Top.root.root',
	'W': 'hists/output/Wjets/hist-Wjets.root.root',
	'Z': 'hists/output/Zjets/hist-Zjets.root.root',
	'Diboson':'hists/output/Diboson/hist-Diboson.root.root',
}


signalsamples = os.listdir("hists/output/")
# print signalsamples
signalsamples = [x for x in signalsamples if "GG_direct" in x or "SS_direct" in x]
# print signalsamples

plottedsignals = {}


plottedsignals["SR2jl"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]
plottedsignals["SR2jm"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]
plottedsignals["SR2jCo"] = ["SS_direct_900_500","SS_direct_1000_600","SS_direct_1100_700" ]
plottedsignals["SR2jt"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]
plottedsignals["SR4jt"] = ["GG_direct_1400_0","GG_direct_1500_100","GG_direct_1600_0" ]
plottedsignals["SR5j"] = ["GG_direct_900_500","GG_direct_1000_600","GG_direct_1100_700" ]
plottedsignals["SR6jm"] = ["GG_direct_900_500","GG_direct_1000_600","GG_direct_1100_700" ]
plottedsignals["SR6jt"] = ["GG_direct_900_500","GG_direct_1000_600","GG_direct_1100_700" ]

plottedsignals["SRS1a"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]
plottedsignals["SRS1b"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]
plottedsignals["SRS2a"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]
plottedsignals["SRS2b"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]
plottedsignals["SRS3a"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]
plottedsignals["SRS3b"] = ["SS_direct_900_0","SS_direct_1000_0","SS_direct_900_200" ]


plottedsignals["SRC1a"] = ["SS_direct_500_450","GG_direct_612_587","GG_direct_650_550" ]
plottedsignals["SRC1b"] = ["SS_direct_500_450","GG_direct_612_587","GG_direct_650_550" ]
plottedsignals["SRC2a"] = ["SS_direct_500_450","GG_direct_612_587","GG_direct_650_550" ]
plottedsignals["SRC2b"] = ["SS_direct_500_450","GG_direct_612_587","GG_direct_650_550" ]
plottedsignals["SRC3a"] = ["SS_direct_500_450","GG_direct_612_587","GG_direct_650_550" ]
plottedsignals["SRC3b"] = ["SS_direct_500_450","GG_direct_612_587","GG_direct_650_550" ]
plottedsignals["SRC4a"] = ["SS_direct_500_450","GG_direct_612_587","GG_direct_650_550" ]
plottedsignals["SRC4b"] = ["SS_direct_500_450","GG_direct_612_587","GG_direct_650_550" ]


plottedsignals["SRG1a"] = ["GG_direct_900_500","GG_direct_1000_600","GG_direct_1100_700" ]
plottedsignals["SRG1b"] = ["GG_direct_900_500","GG_direct_1000_600","GG_direct_1100_700" ]
plottedsignals["SRG1c"] = ["GG_direct_1100_500","GG_direct_1200_600","GG_direct_1200_800" ]
plottedsignals["SRG2a"] = ["GG_direct_1200_400","GG_direct_1300_300","GG_direct_1400_600" ]
plottedsignals["SRG2b"] = ["GG_direct_1200_400","GG_direct_1300_300","GG_direct_1400_600" ]
plottedsignals["SRG2c"] = ["GG_direct_1200_400","GG_direct_1300_300","GG_direct_1400_600" ]
plottedsignals["SRG3a"] = ["GG_direct_1400_0","GG_direct_1500_100","GG_direct_1600_0" ]
plottedsignals["SRG3b"] = ["GG_direct_1400_0","GG_direct_1500_100","GG_direct_1600_0" ]
plottedsignals["SRG3c"] = ["GG_direct_1400_0","GG_direct_1500_100","GG_direct_1600_0" ]


plottedsignals["CRDB1B"] = ["_1400_0","_1500_100","_1600_0" ]


# style_mpl()
fig = plt.figure(figsize=(7,7), dpi=100)




regions = [
# "SR2jt",


"SRS1a",
"SRS1b",
"SRS2a",
"SRS2b",
"SRS3a",
"SRS3b",

"SRC1a",
"SRC1b",
"SRC2a",
"SRC2b",
"SRC3a",
"SRC3b",
"SRC4a",
"SRC4b",

"SRG1a",
"SRG1b",
"SRG1c",
"SRG2a",
"SRG2b",
"SRG2c",
"SRG3a",
"SRG3b",
"SRG3c",


# "SR5j",
# "CRDB1B"
]

for region in regions:

	histogramName = "cutflow_%s"%region

	plt.clf()

	hists = {}
	histsToStack = []
	stack = HistStack()

	for sample in samples:
		f = root_open(myfiles[sample])
		# f.ls()
		hists[sample] = f.Get(histogramName).Clone(sample)
		hists[sample].Sumw2()
		hists[sample].SetTitle(r"%s"%sample)
		# hists[sample].fillstyle = 'solid'
		hists[sample].fillcolor = colors[sample]
		hists[sample].linecolor = colors[sample]
		hists[sample].linewidth = 2
		# hists[sample].Scale(1./hists[sample].GetBinContent(1) )
		if sample != 'Data':
			histsToStack.append( hists[sample] )
		else:
			hists[sample].markersize = 1.2

	sortedHistsToStack = sorted(histsToStack, key=lambda x: x.Integral() , reverse=False)


	mybinlabels = []
	for ibin in xrange(1,hists[samples[0]].GetNbinsX()+1 ):
		# print hists[samples[0]].GetXaxis().GetBinLabel(ibin)
		label = hists[samples[0]].GetXaxis().GetBinLabel(ibin).translate(None, " _(),.").replace("<","$<$").replace(">","$>$")
		mybinlabels.append(  label )

	axes = plt.subplot(211)
	axes.set_yscale('log')
	ylim([1e-7,1e7])

	axes.set_xticks(np.arange( hists[samples[0]].GetNbinsX()  )+0.5 )
	# ax.set_xticklabels( ('G1', 'G2', 'G3', 'G4', 'G5') )
	axes.set_xticklabels( mybinlabels, rotation=90 )
	plt.setp( axes.get_xticklabels(), visible=False)


	cutflows = {}
	for tmphist in sortedHistsToStack:
		if tmphist.Integral():
			stack.Add(tmphist)
			rplt.hist(tmphist, alpha=0.5, emptybins=False)

			if makeCutFlowTables:
				cutflows[tmphist.GetTitle()] = cutFlowTools.histToCutFlow(tmphist)

	for tmphist in sortedHistsToStack:
		print "%s : %f"%(tmphist.GetTitle(), tmphist.GetBinContent(tmphist.GetNbinsX() ) / stack.sum.GetBinContent(stack.sum.GetNbinsX() ) ) 


	cutFlowTools.dictToTable(cutflows, "CutFlowBG%s"%region)


	axes2 = subplot(212, sharex=axes)
	axes2.set_yscale('log')
	ylim([1e-7,2])

	axes2.set_xticks(np.arange( hists[samples[0]].GetNbinsX()  )+0.5 )
	# ax.set_xticklabels( ('G1', 'G2', 'G3', 'G4', 'G5') )
	axes2.set_xticklabels( mybinlabels, rotation=90 )



	for tmphist in sortedHistsToStack:
		if tmphist.Integral():
			# stack.Add(tmphist)
			tmphist.Scale(1./tmphist.GetBinContent(1) )
			rplt.hist(tmphist, alpha=0.5, emptybins=False)

	fig.subplots_adjust(hspace=0.01)
	# rplt.errorbar(hists['Data'], xerr=False, emptybins=False, axes=axes)

	# ylim([1e-7,2])
	plt.subplots_adjust(left=0.1, right=0.9, top=0.98, bottom=0.45)


	cutflows = {}

	for signalsample in signalsamples:
		skip = 1
		if any([thissig in signalsample for thissig in plottedsignals[region]  ]):
			skip=0
		if skip:
			continue
		signalfile = root_open("hists/output/%s/hist-%s.root.root"%(signalsample,  "_".join(signalsample.split("_")[:2])  ) )
		try:
			hists[signalsample] = signalfile.Get(histogramName).Clone( signalsample )
			hists[signalsample].SetTitle(r"%s"%signalsample.replace("_"," ").replace("SRAll","")   )
			
			if makeCutFlowTables:
				cutflows[hists[signalsample].GetTitle()] = cutFlowTools.histToCutFlow(hists[signalsample])

			rplt.errorbar(hists[signalsample], axes=axes, yerr=False, xerr=False, alpha=0.9, fmt="--", markersize=0)
			hists[signalsample].Scale(1./hists[signalsample].GetBinContent(1)  )
			rplt.errorbar(hists[signalsample], axes=axes2, yerr=False, xerr=False, alpha=0.9, fmt="--", markersize=0)
			print "%s %f"%(signalsample, hists[signalsample].Integral()  )
		except:
			continue


	cutFlowTools.dictToTable(cutflows, "CutFlowSig%s"%region)


	axes.annotate(r'\textbf{\textit{ATLAS}} Internal',xy=(0.4,0.90),xycoords='axes fraction') 
	axes.annotate(r'$\sqrt{s}$=13 TeV, %s'%region,xy=(0.65,0.90),xycoords='axes fraction') 



	# get handles
	handles, labels = axes.get_legend_handles_labels()
	# remove the errorbars
	# handles = [h[0] for h in handles]
	for myhandle in handles:
		try:
			myhandle = myhandle[0]
		except:
			pass

	# use them in the legend
	for isignal in xrange(len(plottedsignals[region]) ):
		try:
			handles[-1-isignal] = handles[-1-isignal][0]

		except:
			pass


	# # get handles
	# handles, labels = axes.get_legend_handles_labels()
	# # remove the errorbars
	# tmphandles = []
	# tmplabels = []
	# for a,b in zip(handles,labels):
	# 	# if type(a)==Line2D:
	# 	# 	continue
	# 	tmphandles.append(a[0])
	# 	tmplabels.append(b)
	# # use them in the legend


	axes2.legend(handles, labels, loc='best',numpoints=1)



	axes.set_ylabel('Events / fb-1')
	axes2.set_ylabel('Cut Flow Efficiency')

	# plt.show()

	print "saving"
	fig.savefig("CutflowPlots/%s.pdf"%histogramName, dpi=300)


