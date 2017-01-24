#!/usr/bin/env python

########### Initialization ######################################
##
##

import ROOT
import logging, shutil, os, re, itertools

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
parser.add_option("-n", "--ncores", dest="ncores", default="1",
                  help="number of cpus to use")
(options, args) = parser.parse_args()

ncores = min(4,options.ncores)

import json

with open(options.inputJSONFileName) as inputJSONFile:
    inputJSON = json.load(inputJSONFile)


treeNames = inputJSON["treeNames"]
regions = inputJSON["selections"]

for treeName in treeNames:

	for inputTreeObject in inputJSON["inputTrees"]:
		inputTreeName = inputTreeObject["name"]
		inputTreeFileDirectory = inputTreeObject["directory"]
		inputTreeFileName = inputTreeObject["filename"]

		my_SHs[inputTreeName] = ROOT.SH.SampleHandler()
		ROOT.SH.ScanDir().sampleDepth(0).samplePattern(inputTreeFileName).scan(my_SHs[inputTreeName], inputTreeFileDirectory)
		my_SHs[inputTreeName].setMetaString("nc_tree", "%s"%treeName )

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
			cutlist = regions[region]

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
				job[SH_name].algsAdd(
	            	ROOT.MD.AlgHist(
	            		name = "{0}_{1}".format(commonPlot["xvar"].replace("/","_over_"),region)
	            		ROOT.TH1F( name, name, *commonPlot["xlimits"]),
						commonPlot["xvar"],
						weightstring+"*"+"*".join(regions[region])
						)
					)

			# for varname,varlimits in commonPlots2D.items():
			# 	job[SH_name].algsAdd(
	  #           	ROOT.MD.AlgHist(
	  #           		ROOT.TH2F("%s_%s_%s"%(varname[0].replace("/","_over_"), varname[1].replace("/","_over_"), region), "%s_%s_%s"%(varname[0], varname[1], region), varlimits[0][0], varlimits[0][1], varlimits[0][2], varlimits[1][0], varlimits[1][1], varlimits[1][2]),
			# 			varname[0], varname[1],
			# 			weightstring+"*%s"%regions[region]
			# 			)
			# 		)

			# for varname,varlimits in commonPlots3D.items():
			# 	job[SH_name].algsAdd(
	  #           	ROOT.MD.AlgHist(
	  #           		ROOT.TH3F("%s_%s_%s_%s"%(varname[0].replace("/","_over_"), varname[1], varname[2], region), 
	  #           			"%s_%s_%s_%s"%(varname[0].replace("/","_over_"), varname[1], varname[2], region), 
	  #           			varlimits[0][0], varlimits[0][1], varlimits[0][2], 
	  #           			varlimits[1][0], varlimits[1][1], varlimits[1][2],
	  #           			varlimits[2][0], varlimits[2][1], varlimits[2][2],
	  #           			),
			# 			varname[0], varname[1], varname[2],
			# 			weightstring+"*%s"%regions[region]
			# 			)
			# 		)

	driver = ROOT.EL.DirectDriver()

	for SH_name, mysamplehandler in my_SHs.iteritems():
		if not os.path.exists( "output/%s"%( regionName ) ):
			os.makedirs( "output/%s/"%( regionName ) )
		if os.path.exists( "output/%s/%s"%( regionName, SH_name ) ):
			shutil.rmtree( "output/%s/%s"%( regionName, SH_name ) )
		jobs.append(job[SH_name])
		outputDirs.append("output/%s/%s"%( regionName, SH_name ) )


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

for regionName in regionNames:
	os.system("tar cvzf {0}.tgz output/{0}/*/hist-*.root".format( regionName )   )




# blindSR = False

# # "DV_rxy" = "sqrt(DV_x*DV_x+DV_y*DV_y)"
# DV_phi = "TVector2::Phi_0_2pi(TMath::ATan(DV_y/DV_x) )"

# commonPlots  = {
# "Length$(DV_m)" : [20, 0, 20],
# "DV_nLRT"         : [25, 0, 25],
# "DV_nTracks"      : [50, 0, 50],
# "DV_m"        : [50, 0, 500],
# "DV_r"      : [50, 0, 1000],
# "DV_rxy"      : [100, 0, 500],
# "DV_lastCut"  : [21, -1, 20],
# "DV_chisqPerDoF"  : [50, 0, 10],
# "MET"   : [50, 0, 2000],
# "MEff"  : [50, 0, 5000],
# "HT"    : [50, 0, 5000],
# }


# commonPlots2D  = {
# ("DV_x","DV_y") : ( [300, -150, 150] , [300, -150, 150] ),
# (DV_phi,"DV_rxy") : ( [300, 0, 6.3]    , [300, 0, 300] ),
# ("DV_z","DV_rxy") : ( [300, -300, 300] , [300, 0, 300] ),
# ("DV_nTracks","DV_m") : ( [50, 0, 50] , [50, 0, 500] ),
# ("DV_nLRT","DV_m")    : ( [50, 0, 50] , [50, 0, 500] ),
# ("DV_rxy","DV_m")    : ( [50, 0, 300] , [50, 0, 500] ),
# }


# commonPlots3D  = {
# ("DV_x","DV_y","DV_z") : ( [100, -150, 150] , [100, -150, 150] , [150, -300, 300] ),
# # ("DV_x","DV_y","DV_z") : ( [300, -150, 150] , [300, -150, 150] , [150, -300, 300] ),
# # (DV_phi,"DV_rxy","DV_z") : ( [50, 0, 6.3] , [50, 0, 300] , [50, -300, 300] ),
# }


# ## Define your cut strings here....
# regions = {
# 	"SR0": "( DV_m > -1 )",
# 	"SR1": "( DV_lastCut < 0 )",
# }


# ##
# ###################################################################




# print "\n++++++++++++++++++++++++++++++++++++++++++++++\n\n"
# print "List of region names to run over: " 
# print regionNames


# ## This weird wrapper structure is for the sake of parallelization later ##
# ##

# def submitTheThing(driver,job,directory):
# 	driver.submit(job, directory )

# def submitTheThingWrapper(stuff):
# 	submitTheThing(*stuff)


# jobs = []
# outputDirs = []

# ## Loop over different trees
# for regionName in regionNames:

# 	print "Running over region: %s"%regionName


# 	job = {}

# 	for SH_name, mysamplehandler in my_SHs.iteritems():
# 		print SH_name

# 		job[SH_name] = ROOT.EL.Job()
# 		job[SH_name].sampleHandler(mysamplehandler)

# 		cutflow = {}

# 		if "ata" in SH_name:
# 			weightstring = "(1)"
# 		else:
# 			weightstring = "(normweight*mcEventWeight*pileupWeight)"

# 		for region in regions:

# 			# cutlist = regions[region][1:-1].split("&&")
# 			cutlist = regions[region].split("&&")

# 			cutflow[region] = ROOT.TH1F ("cutflow_%s"%region, "cutflow_%s"%region, len(cutlist)+1 , 0, len(cutlist)+1)
# 			cutflow[region].GetXaxis().SetBinLabel(1, weightstring)


# 			for i,cutpart in enumerate(cutlist):

# 				# print cutpart
# 				if "RunNumber" in cutpart:
# 					continue

# 				cutpartname = cutpart.translate(None, " (),.")
# 				cutpartname = cutpartname.replace("*","_x_").replace("/","_over_")
# 				cutpartname = cutpartname.split("<=")[0].split(">=")[0].split("==")[0]\
# 											.split("<")[0].split(">")[0]

# 				variablename = cutpart.split("<=")[0].split(">=")[0].split("==")[0]\
# 											.split("<")[0].split(">")[0].replace("((","(").replace("( abs","abs")


# 				limits = (10,0,10)

# 				cutflow[region].GetXaxis().SetBinLabel (i+2, cutpart);

# 			job[SH_name].algsAdd(ROOT.MD.AlgCFlow (cutflow[region]))

# 			## each of this histograms will be made for each region
# 			for varname,varlimits in commonPlots.items() :
# 				job[SH_name].algsAdd(
# 	            	ROOT.MD.AlgHist(
# 	            		ROOT.TH1F(varname.replace("/","_over_")+"_%s"%region, varname+"_%s"%region, varlimits[0], varlimits[1], varlimits[2]),
# 						varname,
# 						weightstring+"*%s"%regions[region]
# 						)
# 					)

# 			for varname,varlimits in commonPlots2D.items():
# 				job[SH_name].algsAdd(
# 	            	ROOT.MD.AlgHist(
# 	            		ROOT.TH2F("%s_%s_%s"%(varname[0].replace("/","_over_"), varname[1].replace("/","_over_"), region), "%s_%s_%s"%(varname[0], varname[1], region), varlimits[0][0], varlimits[0][1], varlimits[0][2], varlimits[1][0], varlimits[1][1], varlimits[1][2]),
# 						varname[0], varname[1],
# 						weightstring+"*%s"%regions[region]
# 						)
# 					)

# 			for varname,varlimits in commonPlots3D.items():
# 				job[SH_name].algsAdd(
# 	            	ROOT.MD.AlgHist(
# 	            		ROOT.TH3F("%s_%s_%s_%s"%(varname[0].replace("/","_over_"), varname[1], varname[2], region), 
# 	            			"%s_%s_%s_%s"%(varname[0].replace("/","_over_"), varname[1], varname[2], region), 
# 	            			varlimits[0][0], varlimits[0][1], varlimits[0][2], 
# 	            			varlimits[1][0], varlimits[1][1], varlimits[1][2],
# 	            			varlimits[2][0], varlimits[2][1], varlimits[2][2],
# 	            			),
# 						varname[0], varname[1], varname[2],
# 						weightstring+"*%s"%regions[region]
# 						)
# 					)

# 	driver = ROOT.EL.DirectDriver()

# 	for SH_name, mysamplehandler in my_SHs.iteritems():
# 		if not os.path.exists( "output/%s"%( regionName ) ):
# 			os.makedirs( "output/%s/"%( regionName ) )
# 		if os.path.exists( "output/%s/%s"%( regionName, SH_name ) ):
# 			shutil.rmtree( "output/%s/%s"%( regionName, SH_name ) )
# 		jobs.append(job[SH_name])
# 		outputDirs.append("output/%s/%s"%( regionName, SH_name ) )


# print "Lauching the jobs that are in the list!"

# if ncores>1:
# 	pool = mp.Pool(processes=ncores)
# 	pool.map(submitTheThingWrapper,
# 		itertools.izip( itertools.repeat(driver),
# 			jobs,
# 			outputDirs )
# 		)
# 	pool.close()
# 	pool.join()
# else:
# 	for ijob,job in enumerate(jobs):
# 		print "submitting %d"%ijob
# 		driver.submit(job, outputDirs[ijob] )

# print "Done with jobs. Tarring stuff up..."

# for regionName in regionNames:
# 	os.system("tar cvzf {0}.tgz output/{0}/*/hist-*.root".format( regionName )   )

