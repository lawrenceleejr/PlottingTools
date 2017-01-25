#!/usr/bin/env python

########### Initialization ######################################
##
##

import ROOT
import logging, shutil, os, re, itertools, re

logging.basicConfig(level=logging.INFO)
from optparse import OptionParser

from copy import deepcopy
from collections import OrderedDict
import multiprocessing as mp

import atexit
@atexit.register
def quite_exit():
	ROOT.gSystem.Exit(0)

logging.info("loading packages")
ROOT.gROOT.Macro("$ROOTCOREDIR/scripts/load_packages.C")

ROOT.TH1.SetDefaultSumw2()

##
##
###################################################################


## This weird wrapper structure is for the sake of parallelization later ##
##

def submitTheThing(driver,job,directory):
	driver.submit(job, directory )

def submitTheThingWrapper(stuff):
	submitTheThing(*stuff)


########### Configuration    ######################################
##
##


parser = OptionParser()
parser.add_option("-f", "--file", dest="inputJSONFileName", default="histConfig.json",
                  help="input JSON File")
parser.add_option("-n", "--ncores", dest="ncores", default="3",
                  help="number of cpus to use")
(options, args) = parser.parse_args()

ncores = min(8,options.ncores)

import json

with open(options.inputJSONFileName) as inputJSONFile:
	input_str = inputJSONFile.read()
	input_str = re.sub(r'\\\n', '', input_str)
	input_str = re.sub(r'//.*\n', '\n', input_str)
	inputJSON = json.loads(input_str)


treeNames = inputJSON["treeNames"]
regions = inputJSON["selections"]

jobs = []
outputDirs = []

for treeName in treeNames:

	treeName = str(treeName)

	my_SHs = {}

	for inputTreeObject in inputJSON["inputTrees"]:
		inputTreeName = str(inputTreeObject["name"])
		inputTreeFileDirectory = str(inputTreeObject["directory"])
		inputTreeFileName = str(inputTreeObject["filename"])

		my_SHs[inputTreeName] = ROOT.SH.SampleHandler()
		ROOT.SH.ScanDir().sampleDepth(0).samplePattern(inputTreeFileName).scan(my_SHs[inputTreeName], inputTreeFileDirectory)
		my_SHs[inputTreeName].setMetaString("nc_tree", "%s"%str(treeName) )

	job = {}

	for SH_name, mysamplehandler in my_SHs.iteritems():
		print SH_name

		job[SH_name] = ROOT.EL.Job()
		job[SH_name].sampleHandler(mysamplehandler)

		cutflow = {}

		# if "ata" in SH_name:
		weightstring = "(1)"
		# else:
		# 	weightstring = "(normweight*mcEventWeight*pileupWeight)"

		for region in regions:

			# cutlist = regions[region][1:-1].split("&&")
			cutlist = [str(x) for x in regions[region] ]

			cutflow[region] = ROOT.TH1F ("cutflow_%s"%region, "cutflow_%s"%region, len(cutlist)+1 , 0, len(cutlist)+1)
			cutflow[region].GetXaxis().SetBinLabel(1, weightstring)

			for i,cutpart in enumerate(cutlist):

				# # print cutpart

				# skipCut = False
				# # for extraCut in extraCutsFromChannel:
				# # 	if cutpart.translate(None, " ") in extraCut:
				# # 		skipCut = True
				# # 		break
				# if "RunNumber" in cutpart:
				# 	continue
				# if skipCut:
				# 	continue

				# cutpartname = cutpart.translate(None, " (),.")
				# cutpartname = cutpartname.replace("*","_x_").replace("/","_over_")
				# cutpartname = cutpartname.split("<=")[0].split(">=")[0].split("==")[0]\
				# 							.split("<")[0].split(">")[0]

				# variablename = cutpart.split("<=")[0].split(">=")[0].split("==")[0]\
				# 							.split("<")[0].split(">")[0].replace("((","(").replace("( abs","abs")

				cutflow[region].GetXaxis().SetBinLabel (i+2, cutpart);

			job[SH_name].algsAdd(ROOT.MD.AlgCFlow (cutflow[region]))

			## each of this histograms will be made for each region
			for commonPlot in inputJSON["commonPlots"]:
				name = "{0}_{1}".format(commonPlot["xvar"].replace("/","_over_"),region)
				job[SH_name].algsAdd(
	            	ROOT.MD.AlgHist(
	            		ROOT.TH1F( name, name, *commonPlot["xlimits"]),
						str(commonPlot["xvar"]),
						weightstring+"*"+"*".join(cutlist)
						)
					)

			for commonPlot in inputJSON["commonPlots2D"]:
				name = "{0}_vs_{1}_{2}".format(commonPlot["xvar"].replace("/","_over_"),
												commonPlot["yvar"].replace("/","_over_"),
												region)
				job[SH_name].algsAdd(
	            	ROOT.MD.AlgHist(
	            		ROOT.TH2F( name, name, *(commonPlot["xlimits"]+commonPlot["ylimits"]) ),
						str(commonPlot["xvar"]),
						str(commonPlot["yvar"]),
						weightstring+"*"+"*".join(cutlist)
						)
					)

			for commonPlot in inputJSON["commonPlots3D"]:
				name = "{0}_vs_{1}_vs_{2}_{3}".format(commonPlot["xvar"].replace("/","_over_"),
												commonPlot["yvar"].replace("/","_over_"),
												commonPlot["zvar"].replace("/","_over_"),
												region)
				job[SH_name].algsAdd(
	            	ROOT.MD.AlgHist(
	            		ROOT.TH3F( name, name, *(commonPlot["xlimits"]+commonPlot["ylimits"]+commonPlot["zlimits"])),
						str(commonPlot["xvar"]),
						str(commonPlot["yvar"]),
						str(commonPlot["zvar"]),
						weightstring+"*"+"*".join(cutlist)
						)
					)

	driver = ROOT.EL.DirectDriver()

	for SH_name, mysamplehandler in my_SHs.iteritems():
		if not os.path.exists( "output/%s"%( treeName ) ):
			os.makedirs( "output/%s/"%( treeName ) )
		if os.path.exists( "output/%s/%s"%( treeName, SH_name ) ):
			shutil.rmtree( "output/%s/%s"%( treeName, SH_name ) )
		jobs.append(job[SH_name])
		outputDirs.append("output/%s/%s"%( treeName, SH_name ) )


print "Lauching the jobs that are in the list!"

if ncores>1:
	pool = mp.Pool(processes=ncores)
	pool.map(submitTheThingWrapper,
		itertools.izip( itertools.repeat(driver),
			jobs,
			outputDirs )
		)
	pool.close()
	pool.join()
else:
	for ijob,job in enumerate(jobs):
		print "submitting %d"%ijob
		driver.submit(job, outputDirs[ijob] )

print "Done with jobs. Tarring stuff up..."

for treeName in treeNames:
	os.system("tar cvzf {0}.tgz output/{0}/*/hist-*.root".format( treeName )   )


