#!/usr/bin/env python
import sys,os,math
sys.path.append("/opt/Mantid/bin")
#sys.path.insert(0,"/SNS/software/lib/python2.6/site-packages/matplotlib-1.2.0-py2.6-linux-x86_64.egg")
#from ARLibrary import * #note that ARLibrary would set mantidpath as well


import sys,os
sys.path.append("/opt/mantidnightly/bin")
from numpy import *
from string import *

import mantid


class ExperimentLog(object):
    def __init__(self):
        self.log_list=[]
        self.simple_logs=[]
        self.SERotOptions=[]
        self.SETempOptions=[]
        self.firstLine=''
        self.Filename=''
        self.kwds=[]
                
    def setLogList(self,logstring):
        self.log_list=[a.strip() for a in logstring.split(',')]
        
    def setSimpleLogList(self,logstring):
        self.simple_logs=[a.strip() for a in logstring.split(',')] 
    
    def setFilename(self,fname):
        self.Filename=fname
        
    def setSERotOptions(self,logstring):
        self.SERotOptions=[a.strip() for a in logstring.split(',')]  
               
    def setSETempOptions(self,logstring):
        self.SETempOptions=[a.strip() for a in logstring.split(',')]     
                     
    def log_line_gen(self,IWSName):
        """
        IWSName is a string of the workspace name
        """
        ws=mantid.mtd[IWSName]
        parameterList=[]
        self.firstLine+='RunNumber, '
        parameterList.append(str(ws.getRunNumber()))                                    #run number
        self.firstLine+='Title, '
        parameterList.append(ws.getTitle().replace(' ','_').replace(',','_'))           #title - spaces and commas are replaced by underscores
        self.firstLine+='Comment, '
        parameterList.append(ws.getComment().replace(' ','_').replace(',','_'))         #comment from the file - spaces and commas with underscores
        self.firstLine+='StartTime, '
        parameterList.append(ws.getRun()['start_time'].value)                           #start time
        self.firstLine+='EndTime, '
        parameterList.append(ws.getRun()['end_time'].value)                             #end time
        self.firstLine+='Duration, '
        parameterList.append(str(ws.getRun()['duration'].value))                        #duration
        self.firstLine+='ProtonCharge, '
        parameterList.append(str(ws.getRun().getProtonCharge()))                        #proton charge in microamps*hour
                
        for sLog in self.log_list:
            if ws.getRun().hasProperty(sLog):
                try: #check if it's a time series property
                    stats=ws.getRun()[sLog].getStatistics()
                    if sLog in self.simple_logs:
                        self.firstLine+='%s mean,'%(sLog)
                        parameterList.append(str(stats.mean))
                    else:
                        self.firstLine+='%s mean,%s minimum,%s maximum,%s stddev,'%(sLog,sLog,sLog,sLog)
                        parameterList.append(str(stats.mean))
                        parameterList.append(str(stats.minimum))
                        parameterList.append(str(stats.maximum))
                        parameterList.append(str(stats.standard_deviation))
                except: #not a TSP
                    self.firstLine+='%s,'%(sLog)
                    parameterList.append(ws.getRun()[sLog].valueAsStr)
            else: #could not find that parameter
                if sLog in self.simple_logs:
                    self.firstLine+='%s ,'%(sLog)
                    parameterList.append('N/A')
                else:   
                    self.firstLine+='%s mean,%s minimum,%s maximum,%s stddev,'%(sLog,sLog,sLog,sLog)
                    parameterList.append('N/A')
                    parameterList.append('N/A')
                    parameterList.append('N/A')
                    parameterList.append('N/A')
        

  
        #check for sample environment temperature reading
        for SET in self.SETempOptions:
            if SET not in self.log_list:  #make sure not to write again, if it was in log_list 
                if ws.getRun().hasProperty(SET):
                    self.log_list.append(SET) #next time is in the log_list
                    stats=ws.getRun().getProperty(SET).getStatistics()
                    self.firstLine+='%s mean,%s minimum,%s maximum,%s stddev,'%(SET,SET,SET,SET)
                    parameterList.append(str(stats.mean))
                    parameterList.append(str(stats.minimum))
                    parameterList.append(str(stats.maximum))
                    parameterList.append(str(stats.standard_deviation))

                    
                    
                    
        #check sample environment rotation stage
        angle=0.
        for SE in self.SERotOptions:            
            if ws.getRun().hasProperty(SE):
                stats=ws.getRun().getProperty(SE).getStatistics()
                angle=stats.mean
                if SE not in self.log_list:  #make sure not to write again, if it was in log_list 
                    self.log_list.append(SE) #next time is in the log_list
                    self.firstLine+='%s mean,%s minimum,%s maximum,%s stddev,'%(SE,SE,SE,SE)

                    parameterList.append(str(stats.mean))
                    parameterList.append(str(stats.minimum))
                    parameterList.append(str(stats.maximum))
                    parameterList.append(str(stats.standard_deviation))

        outstr=','.join(parameterList)

        return [outstr,angle]
        
    def save_line(self,IWSName, **kwargs):
        for key,value in kwargs.iteritems():
            if key not in self.kwds:
                self.kwds.append(key)
        
        [outstr,angle]=self.log_line_gen(IWSName)       
        
        header=self.firstLine+','.join(self.kwds)
        outstr+=','
        for k in self.kwds:
            val=kwargs.get(k,None)
            if val==None:
                outstr+='N/A,'
            else:
                outstr+=str(val)+','
                
        try:
            rhandle=open(self.Filename,'r')#see if file is there
            rhandle.close()
        except IOError:
            whandle=open(self.Filename,'w')#if not, write header
            whandle.write(header+'\n')
            whandle.close()
        
        ahandle=open(self.Filename,'a')
        ahandle.write(outstr+'\n')
        ahandle.close()
            
        return angle


from numpy import arange
from mantid import *
from mantid.simpleapi import *


def getEightPackHandle(inst,banknum):
    name=inst.getName()
    banknum=int(banknum)
    if name=="ARCS":
        if     (1<=banknum<= 38):
            return inst[3][banknum-1][0]
        elif  (39<=banknum<= 77):
            return inst[4][banknum-39][0]
        elif  (78<=banknum<=115):
            return inst[5][banknum-78][0]
        else: 
            raise ValueError("Out of range index for ARCS instrument bank numbers")
    elif name=="CNCS":
        if     (1<=banknum<= 50):
            return inst[3][banknum-1][0]
        else: 
            raise ValueError("Out of range index for CNCS instrument bank numbers")
    elif name=="HYSPEC":
        if     (1<=banknum<= 20):
            return inst[3][banknum-1][0]    
        else: 
            raise ValueError("Out of range index for HYSPEC instrument bank numbers")
    elif name=="SEQUOIA":
        if     (38<=banknum<= 74):
            return inst[3][banknum-38][0]
        elif  (75<=banknum<= 113):
            return inst[4][banknum-75][0]
        elif  (114<=banknum<=150):
            return inst[5][banknum-114][0]
        else: 
            raise ValueError("Out of range index for SEQUOIA instrument bank numbers: %s"%banknum)

        
def MaskBTP(**kwargs):

    instrument=kwargs.get('Instrument',None)
    banks=kwargs.get('Bank',None)
    tubes=kwargs.get('Tube',None)
    pixels=kwargs.get('Pixel',None)
    workspace=kwargs.get('Workspace',None)
    detlist=[]
    try:
#    if ((workspace!=None) and (mtd.workspaceExists(workspace) ==True)):
        w=mtd[workspace]
        inst=w.getInstrument()
        instrument =inst.getName()
    except:
        pass
    instrumentList=["ARCS","CNCS","HYSPEC","SEQUOIA"]
    try:
        instrumentList.index(instrument)
    except:
        print "Instrument not found"
        return detlist
    if (workspace==None):
        path=config["instrumentDefinition.directory"]
        LoadEmptyInstrument(Filename=path+instrument+"_Definition.xml",OutputWorkspace="temporaryWorkspaceForMasking")
        workspace="temporaryWorkspaceForMasking"
        w=mtd[workspace]
        inst=w.getInstrument()
    if (banks==None):
        if (instrument=="ARCS"):
            banks=arange(115)+1
        elif (instrument=="CNCS"):
            banks=arange(50)+1
        elif (instrument=="HYSPEC"):
            banks=arange(20)+1
        elif (instrument=="SEQUOIA"):
            banks=arange(113)+38
    else:
        # try to get the bank numbers in an array, even if the banks is string, array, or an integer
        banks=eval(str(banks))
        try:
            len(banks)
        except:
            banks=[banks]
    if(tubes==None):
        tubes=arange(8)+1
    else:
        tubes=eval(str(tubes))
        try:
            len(tubes)
        except:
            tubes=[tubes]
    if(pixels==None):
        pixels=arange(128)+1
    else:
        pixels=eval(str(pixels))
        try:
            len(pixels)
        except:
            pixels=[pixels]    
    for b in banks:
        ep=getEightPackHandle(inst,b)
        for t in tubes:
            if ((t<1) or (t>8)):
                raise ValueError("Out of range index for tube number")
            else:
                for p in pixels:
                    if ((p<1) or (p>128)):
                        raise ValueError("Out of range index for pixel number")
                    else:
                        pid=ep[int(t-1)][int(p-1)].getID()
                        detlist.append(pid)
    MaskDetectors(Workspace=workspace,DetectorList=detlist)
    return detlist

#MaskBTP(Instrument="SEQUOIA",Pixel="1,2,3,4,5,6,7,8,121,122,123,124,125,126,127,128")
#MaskBTP(Workspace="temporaryWorkspaceForMasking",Bank=110)

from mantid.simpleapi import *
from matplotlib import *

use("agg")
from matplotlib.pyplot import *




# Logs at: /var/log/SNS_applications/autoreduce.log
import numpy

def preprocessVanadium(Raw,Processed,Parameters):
    
    Raw = "SEQ_" + Raw + '.nxs.h5'
    
    if os.path.isfile(Processed):
        LoadNexus(Filename=Processed,OutputWorkspace="__VAN")
        dictvan={'UseProcessedDetVan':'1','DetectorVanadiumInputWorkspace':'__VAN'}
    else:
        LoadEventNexus(Filename=Raw,OutputWorkspace="__VAN",Precount=0)
        #ChangeBinOffset(InputWorkspace="__VAN",OutputWorkspace="__VAN",Offset=500,IndexMin=54272,IndexMax=55295) # adjust time for pack C17 wired backward
        for d in Parameters:
            MaskBTP(Workspace="__VAN",**d)
        dictvan={'SaveProcessedDetVan':'1','DetectorVanadiumInputWorkspace':'__VAN','SaveProcDetVanFilename':Processed}
    return dictvan
        
def preprocessData(filename):
    #f1 = os.path.split(filename)[-1]
    #runnum = int(f1.strip('SEQ_').replace('.nxs.h5',''))
    runnum = int(filename)
    filename = "SEQ_" + filename + '.nxs.h5'
    __MonWS=LoadNexusMonitors(Filename=filename)

    #PV streamer not running. Copying logs from some other run
    if (runnum >= 55959 and runnum <= 55960):
        LoadNexusLogs(__MonWS,"/SNS/SEQ/IPTS-10531/nexus/SEQ_55954.nxs.h5")
    
    #FilterByLogValue("__MonWS",OutputWorkspace="__MonWS",LogName="CCR22Rot",MinimumValue=52.2,MaximumValue=52.4)
    Eguess=__MonWS.getRun()['EnergyRequest'].getStatistics().mean
    ###########################
    #Temporary workaround for IPTS-9145  GEG
    if Eguess<5:
      Eguess=120.
    ###################  
    
    if (runnum >= 46951 and runnum <= 46994):

        Efixed = 119.37
        T0 = 25.84

        LoadEventNexus(Filename=filename,OutputWorkspace="__IWS",Precount=0) #Load an event Nexus file
        #Fix that all time series log values start at the same time as the proton_charge
        CorrectLogTimes('__IWS')

        #Filter chopper 3 bad events
        valC3=__MonWS.getRun()['Phase3'].getStatistics().median

        MaskBTP(workspace='__IWS', Bank='38-57,75-94')

        return [Eguess,Efixed,T0]
    
    try:   
             sp1=-1
             sp2=-1
             nsp=__MonWS.getNumberHistograms()                
             if nsp < 2:
                 raise ValueError("There are less than 2 monitors")
             for sp in range(nsp):
                 if __MonWS.getSpectrum(sp).getDetectorIDs()[0]==-1:
                     sp1=sp
                 if __MonWS.getSpectrum(sp).getDetectorIDs()[0]==-2:
                     sp2=sp
             if sp1==-1:
                 raise RuntimeError("Could not find spectrum for the first monitor")
             if sp2==-1:
                 raise RuntimeError("Could not find spectrum for the second monitor")       
             so=__MonWS.getInstrument().getSource().getPos()
             m1=__MonWS.getDetector(sp1).getPos()
             m2=__MonWS.getDetector(sp2).getPos()
             v=437.4*numpy.sqrt(__MonWS.getRun()['EnergyRequest'].getStatistics().mean)
             t1=m1.distance(so)*1e6/v
             t2=m2.distance(so)*1e6/v
             t1f=int(t1*60e-6) #frame number for monitor 1
             t2f=int(t2*60e-6) #frame number for monitor 2
             wtemp=ChangeBinOffset(__MonWS,t1f*16667,sp1,sp1)
             wtemp=ChangeBinOffset(wtemp,t2f*16667,sp2,sp2)
             wtemp=Rebin(InputWorkspace=wtemp,Params="1",PreserveEvents=True)
             
             #check whether the fermi chopper is in the beam
             fermi=__MonWS.run().getProperty('vChTrans').value[0]

             if fermi == 2 :
                 Efixed = nan
                 T0 = nan
                 DeleteWorkspace(wtemp)

             if fermi != 2:
                 alg=GetEi(InputWorkspace=wtemp,Monitor1Spec=sp1+1,Monitor2Spec=sp2+1,EnergyEstimate=Eguess)   #Run GetEi algorithm
                 Efixed=alg[0]
                 T0=alg[3]                                        #Extract incident energy and T0
                 DeleteWorkspace(wtemp)
    except e:    
            [Efixed,T0]=GetEiT0atSNS("__MonWS",Eguess)

    #if Efixed!='N/A':
    LoadEventNexus(Filename=filename,OutputWorkspace="__IWS",Precount=0) #Load an event Nexus file
    if (runnum >= 55959 and runnum <= 55960):
        LoadNexusLogs("__IWS","/SNS/SEQ/IPTS-10531/nexus/SEQ_55954.nxs.h5")
    #Fix that all time series log values start at the same time as the proton_charge
    CorrectLogTimes('__IWS')
    #adjust data times for addl frames
    td=25.5*1e6/v
    if (td > 16666.7):
        tdf=int(td*60e-6)
        ChangeBinOffset(InputWorkspace='__IWS', OutputWorkspace='__IWS', Offset=16667*tdf)

    #FilterByLogValue("__IWS",OutputWorkspace="__IWS",LogName="CCR22Rot",MinimumValue=52.2,MaximumValue=52.4)
    #Filter chopper 3 bad events
    valC3=__MonWS.getRun()['Phase3'].getStatistics().median
    #FilterByLogValue(InputWorkspace='__IWS',OutputWorkspace='__IWS',LogName='Phase3',MinimumValue=valC3-0.15,MaximumValue=valC3+0.15)
    #FilterBadPulses(InputWorkspace="__IWS",OutputWorkspace = "__IWS",LowerCutoff = 50)
    return [Eguess,Efixed,T0]
  
    
def WS_clean():
    DeleteWorkspace('__IWS')
    DeleteWorkspace('__OWS')
    DeleteWorkspace('__VAN')
    DeleteWorkspace('__MonWS')
    
          
if __name__ == "__main__":
    numpy.seterr("ignore")#ignore division by 0 warning in plots
    #processing parameters
    RawVanadium="{{raw_vanadium}}"
    ProcessedVanadium="{{processed_vanadium}}"
    HardMaskFile=''
    IntegrationRange=[0.3,1.2] #integration range for Vanadium in angstroms
    
    MaskBTPParameters=[]
    {% if masked_bank %}
    MaskBTPParameters.append({'Bank':"{{masked_bank}}"})
    {% endif %}
    {% if masked_tube %}
    MaskBTPParameters.append({'Tube':"{{masked_tube}}"})
    {% endif %}
    {% if masked_pixel %}
    MaskBTPParameters.append({'Pixel':"{{masked_pixel}}"})
    {% endif %}

 # only for the runs in IPTS-11831
 #   MaskBTPParameters.append({'Bank':"61-74,98-113,137-150"})
    
    clean=True
    NXSPE_flag=True

    NormalizedVanadiumEqualToOne = True
        
    filename = "{{data_file}}"
    outdir = "{{output_path}}"

    elog=ExperimentLog()
    elog.setLogList('vChTrans,Speed1,Phase1,Speed2,Phase2,Speed3,Phase3,EnergyRequest,s1t,s1r,s1l,s1b,vAttenuator2,vAttenuator1,svpressure,dvpressure')
    elog.setSimpleLogList("vChTrans, EnergyRequest, s1t, s1r, s1l, s1b, vAttenuator2, vAttenuator1")
    elog.setSERotOptions('CCR13VRot, SEOCRot, CCR16Rot, CCR22Rot')
    elog.setSETempOptions('SampleTemp, sampletemp, SensorA, SensorA340 ')
    elog.setFilename(outdir+'experiment_log.csv')

    processed_van_file = ProcessedVanadium
    if not os.path.isabs(processed_van_file):
        processed_van_file = os.path.join(outdir, ProcessedVanadium)

    DGSdict=preprocessVanadium(RawVanadium, processed_van_file, MaskBTPParameters)
    #--------------------------------------
    #Preprocess data to get Ei and T0
    #--------------------------------------
    [EGuess,Ei,T0]=preprocessData(filename)
    angle=elog.save_line('__MonWS',CalculatedEi=Ei,CalculatedT0=T0)    #If angles not saved to file, put them by hand here and re-run reduction one by one.
    #angle= 99.99 #This is where you can manually set the rotation angle
    outpre='SEQ'
    runnum=str(mtd['__IWS'].getRunNumber()) 
    outfile=outpre+'_'+runnum+'_autoreduced'
    if not math.isnan(Ei):
        DGSdict['SampleInputWorkspace']='__IWS'
        DGSdict['SampleInputMonitorWorkspace']='__MonWS'
        DGSdict['IncidentEnergyGuess']=Ei
        DGSdict['UseIncidentEnergyGuess']='1'
        DGSdict['TimeZeroGuess']=T0
        DGSdict['EnergyTransferRange']=[{{ energy_binning_min }}*EGuess,
                                        {{ energy_binning_step }}*EGuess,
                                        {{ energy_binning_max }}*EGuess]  #Typical values are -0.5*EGuess, 0.005*EGuess, 0.95*EGuess
        DGSdict['SofPhiEIsDistribution']='0' # keep events
        DGSdict['HardMaskFile']=HardMaskFile
        DGSdict['GroupingFile']="{{grouping_file}}"#'/SNS/SEQ/shared/autoreduce/SEQ_2x2_grouping.xml' #Typically an empty string '', choose 2x1 or some other grouping file created by GenerateGroupingSNSInelastic or GenerateGroupingPowder
        DGSdict['IncidentBeamNormalisation']='None'  #NEXUS file does not have any normaliztion, but the nxspe IS normalized later in code by charge
        DGSdict['UseBoundsForDetVan']='1'
        DGSdict['DetVanIntRangeHigh']=IntegrationRange[1]
        DGSdict['DetVanIntRangeLow']=IntegrationRange[0]
        DGSdict['DetVanIntRangeUnits']='Wavelength'
        DGSdict['OutputWorkspace']='__OWS'
        DgsReduction(**DGSdict)
        

        #Do normalization of vanadum to 1
        # This step only runs ONCE if the processed vanadium file is not already present.
        if DGSdict.has_key('SaveProcessedDetVan') and NormalizedVanadiumEqualToOne:
              filename=DGSdict['SaveProcDetVanFilename']
              LoadNexus(Filename=filename,OutputWorkspace="__VAN")
              datay = mtd['__VAN'].extractY()
              meanval = float(datay[datay>0].mean())
              CreateSingleValuedWorkspace(OutputWorkspace='__meanval',DataValue=meanval)
              Divide(LHSWorkspace='__VAN',RHSWorkspace='__meanval',OutputWorkspace='__VAN') #Divide the vanadium by the mean
              Multiply(LHSWorkspace='__OWS',RHSWorkspace='__meanval',OutputWorkspace='__OWS') #multiple by the mean of vanadium Normalized data = Data / (Van/meanvan) = Data *meanvan/Van
              SaveNexus(InputWorkspace="__VAN", Filename= filename)        
        
        
        AddSampleLog(Workspace="__OWS",LogName="psi",LogText=str(angle),LogType="Number")
        SaveNexus(InputWorkspace="__OWS", Filename= outdir+outfile+".nxs")
        RebinToWorkspace(WorkspaceToRebin="__OWS",WorkspaceToMatch="__OWS",OutputWorkspace="__OWS",PreserveEvents='0')
        NormaliseByCurrent(InputWorkspace="__OWS",OutputWorkspace="__OWS")
        ConvertToDistribution(Workspace="__OWS")                                                                         #Divide by bin width
#generate summed spectra_plot
#---------------------------------------          
        s=SumSpectra("__OWS")
        x=s.readX(0)
        y=s.readY(0)
        plot(x[1:],y)
        xlabel('Energy transfer (meV)')
        ylabel('Intensity')
        yscale('log')
        show()
        savefig(outdir+outfile+'nxs.png',bbox_inches='tight')
        
        if NXSPE_flag:            
            SaveNXSPE(InputWorkspace="__OWS", Filename= outdir+outfile+".nxspe",Efixed=Ei,Psi=angle,KiOverKfScaling=True) 
        if clean:
            WS_clean()
    else:
       ConvertUnits(InputWorkspace="__IWS",OutputWorkspace="__IWS",Target='dSpacing')
       Rebin(InputWorkspace="__IWS",OutputWorkspace="__OWS",Params='0.5,0.005,10',PreserveEvents='0')
       SaveNexus(InputWorkspace="__OWS", Filename= outdir+outfile+".nxs")
                                                    

            