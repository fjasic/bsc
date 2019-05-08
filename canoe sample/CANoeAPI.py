# -----------------------------------------------------------------------------
# # Copyright (C) 2013 TTTech Computertechnik AG. All rights reserved
# Schoenbrunnerstrasse 7, A--1040 Wien, Austria. office@tttech.com
#
# ++
# Name
#    CANoeAPI
#
# Purpose
#    API for Vector CANoe.
#
#
# Revision Dates
#      29-Jan-2016 eVTE: Creation. Implementation of CANoeAPI class.
#      01-Feb-2016 eVTE: Implementation of CANoeTestConfigurationEvents class.
#      02-Feb-2016 eVTE: Implementation of functions ActivateSingleTest and
#        ActivateSingleNode
#      04-Feb-2016 eVTE: Implementation of function EnableXCP
#      05-Feb-2016 eVTE: Implementation of functions SetValueOfSysvar,
#        GetValueOfSysvar, GetNamespaceObj, GetSysvarObj
#      05-Apr-2016 eVTE: Implementation of functions SendDiagRequest
#      15-Jul-2016 eVTE: Implementation of functions ConfigFlexRayNetwork,
#        SendDiagRequestExpectDTC, SendDiagRequestExpectDTC
#
# Status: Development
# -----------------------------------------------------------------------------

import sys
import pythoncom
import win32com.client
import psutil
import os
import threading
import time
from test_config import HOST_MAP, XCPdevice


def canoe_exe_thread(te_obj, stop_event):
    while not stop_event.is_set():
        if te_obj.CANoe is not None and te_obj.CANoe.request['callback'] is not None:
            try:
                te_obj.CANoe.request['response_data'] = te_obj.CANoe.request['callback'](
                    *te_obj.CANoe.request['args'],
                    **te_obj.CANoe.request['kwargs']
                    )
            except Exception as e:
                te_obj.log.error("Error detected in thread 'canoe_exe_thread', %s: %s" %
                                 (te_obj.CANoe.request['callback'], e))

            te_obj.CANoe.request['response_ready'] = True
            te_obj.CANoe.request['callback'] = None



def func_wrapper(callback):
    def wrapper(self, *args, **kwargs):
        return_value = None
        if te_obj.threads['canoe_exe_thread']['Thread'] == threading.current_thread():
            return_value = callback(self, *args, **kwargs)
        else:
            self.request['args'] = (self,) + args
            self.request['kwargs'] = kwargs
            self.request['callback'] = callback
            start_ts = time.time()
            while (self.request['response_ready'] is False and
                    time.time() < start_ts + 300):
                pass
            return_value = self.request['response_data']
            self.request['response_ready'] = False
            self.request['args'] = tuple()
            self.request['kwargs'] = dict()
        return return_value
    return wrapper


class Diag(object):
    def __init__():
        print "CANoe API BASE"
        super(Diag, self).__init__()


    @func_wrapper
    def InitDiagnostic(self, testerPresent=True, log=True):
        """Initialize diagnostics.

        From defined FlexRay network, get diagnostic object and activate
        tester present status

        :type testerPresent: bool
        :param testerPresent: Set TesterPresent to on or off

        :type log: bool
        :param log: Write tester present status (Default value = True)

        :rtype: diagnostic device object
        :returns: Diagnostic device object
        """
        if self.diagDev is None:
            try:
                netw = self.CANoe.Networks(self.DiagNetwork)
                self.diagDev = netw.Devices(self.DiagDeviceName).Diagnostic
            except Exception as e:
                self.log.error("Failed to initalize diagnostic (" + str(e) + ")")

        if self.diagDev is not None:
            if testerPresent:
                self.diagDev.DiagStartTesterPresent()
            else:
                self.diagDev.DiagStopTesterPresent()
            if log:
                self.log.debug("\nTester present status: %s"
                            % self.diagDev.TesterPresentStatus)
        return self.diagDev

    @func_wrapper
    def TesterPresent(self, log=True):
        """Check tester present status.

        :type log: bool
        :param log: Write tester present status (Default value = True)

        :rtype: bool
        :returns: Tester present status
        """

        diagDev = self.InitDiagnostic(log)
        return diagDev.TesterPresentStatus

    @func_wrapper
    def SendDiagnosticRequest(self, diagRequestString):
        """Send diagnostic request.

        :type diagRequestString: string
        :param diagRequestString: Name of the diagnostic request

        :rtype: bool
        :returns: Diagnostic response
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest(diagRequestString)
        resp = self.SendRequestWaitResponse(diagReq)
        return self.CheckResponse(resp)

    @func_wrapper
    def SendRequestWaitResponse(self, diagReq):
        """Send diagnostic request and wait for response.

        :type diagReq: DiagnosticRequest object
        :param diagReq: DiagnosticRequest object

        :rtype: bool
        :returns: Diagnostic response, None if there is no response
        """

        diagReq.Send()

        counter = 0
        while diagReq.Pending and counter < 60:
            time.sleep(0.5)
            counter += 1

        if diagReq.Responses.Count == 0:
            self.log.warning("No Response received!")
            diagReq.Send()

            counter = 0
            while diagReq.Pending and counter < 60:
                time.sleep(0.5)
                counter += 1

        if diagReq.Responses.Count == 0:
            self.log.warning("No Response received!")
            return None
        else:
            response = diagReq.Responses(1)
            return response

    @func_wrapper
    def CheckResponse(self, resp, log=True):
        """Check diagnostic response.

        :type resp: DiagnosticResponse object
        :param resp: DiagnosticResponse object

        :type log: bool
        :param log: Write response status (Default value = True)

        :rtype: bool
        :returns: True if diagnostic response is positive, False if not
        """

        if resp is not None:
            if resp.Positive:
                if log:
                    self.log.debug("Positive response received!\n")
                return True
            else:
                if log:
                    self.log.debug("Negative response received!\n")
                return False


class XCP(object):
    def __init__():
        super(XCP, self).__init__()

    @func_wrapper
    def ConnectXCP(self, host):
        """Connect XCP device for desired host.

        :type host: string
        :param host: name of the host

        .. note:: parameter host can have values [APH, SSH, SRH, APHFR]
        *APHFR = XCP over FlexRay on APH
        """

        ecuIndex = HOST_MAP.index(host) + 1
        self.log.debug("Connecting device...")
        self.SetValueOfSysvar(ecuIndex, "ConnectXCP", "XCP_Access")

    @func_wrapper
    def DisconnectXCP(self, host):
        """Disconnect XCP device for desired host.

        :type host: string
        :param host: name of the host

        .. note:: parameter host can have values [APH, SSH, SRH, APHFR]
        *APHFR = XCP over FlexRay on APH
        """

        ecuIndex = HOST_MAP.index(host) + 1
        self.log.debug("Disconnecting device...")
        self.SetValueOfSysvar(ecuIndex, "DisconnectXCP", "XCP_Access")

    @func_wrapper
    def IsXCPConnected(self, host):
        """Check if XCP is connected for desired host.

        :type host: string
        :param host: name of the host

        :rtype: bool
        :returns: Connection status, None if there is no active device

        .. note:: parameter host can have values [APH, SSH, SRH, APHFR]
        *APHFR = XCP over FlexRay on APH
        """
        value = self.GetValueOfSysvar("IsXcpConnected%s" % host, "XCP_Access")
        if value == 1:
            return True
        elif value == 0:
            return False
        else:
            self.log.error("Device doesn't exist or it's not active!")
            return None

    @func_wrapper
    def CheckXCPconnection(self, namespace):
        """Check if XCP is connected for desired namespace.

        :type namespace: string
        :param namespace: namespace of the XCP ECU

        :rtype: bool
        :returns: Connection status, None if there is no active device
        """
        hostLst = [k[0] for k in self.XCPns.items() if k[1] == namespace]
        if len(hostLst) > 0:
            if self.IsXCPConnected(hostLst[0]) is not True:
                self.log.error("XCP on %s is not connected!" % hostLst[0])
                return False
        return True
    
    @func_wrapper
    def ActivateECUOnHost(self, host):
        """Activate XCP ECU object on desired host (deactivate all others).

        :type host: string
        :param host: name of the host [APH, SSH, SRH, APHFR]
        (APHFR is used for XCP over FlexRay on APH)
        """

        self.ECUObj = self.GetAllECUs()

        if host != 'APHFR':
            for hostL in ['APH', 'SSH', 'SRH']:
                if self.ECUObj[hostL] is not None:
                    if host == hostL:
                        self.ActivateECU(self.ECUObj[hostL])
                    else:
                        self.DeactivateECU(self.ECUObj[hostL])

            if self.ECUObj['APHFR'] is not None:
                if host == 'APH':
                    self.DeactivateECU(self.ECUObj['APHFR'])
                else:
                    self.ActivateECU(self.ECUObj['APHFR'])

        else:
            activeECU = self.GetActiveECU()
            if activeECU is not None:
                if 'ApplicationHost' in activeECU.Name:
                    self.DeactivateECU(self.ECUObj['APH'])
            self.ActivateECU(self.ECUObj['APHFR'])

    @func_wrapper
    def EnableXCPParam(self, ECU, paramName, enableAll=False, mode='Poll'):
        """Enable single XCP parameter.

        :type ECU: McECU
        :param ECU: XCP ECU object

        :type paramName: string
        :param paramName: name of the XCP parameter

        :type enableAll: bool
        :param enableAll: enable parameter of any type (Default value = False)

        :type mode: string
        :param mode: read mode of the parameter ['Poll', 'DAQ']
        (Default value = 'Poll')
        """

        ECUname = ECU.Name
        # TODO Item(1)=BIST, counting through items and find specific
        try:
            parameter = ECU.MeasurementGroups.Item(1).Parameters(paramName)
        except:
            self.log.error("Could not find specified parameter!")
            return None

        parameter.Configured = 1
        if mode == 'Poll':
            parameter.ReadMode = 1
            parameter.EventCycle = 100
        else:
            parameter.ReadMode = 2
            if paramName.count(".") <= 1:
                parameter.EventCycle = 1
            else:
                parameter.EventCycle = 2  # or 3???

        newParamName = paramName.replace(".", "_")
        newParamName = newParamName.replace("[", "_")
        newParamName = newParamName.replace("]", "_")
        varObj = self.GetSysvarObj(newParamName, "XCP::%s" % ECUname)
        try:
            newObj = win32com.client.CastTo(varObj, "IVariable8")
        except Exception as e:
            print e
            self.log.error("Error while enabling test point: {0}, namespace XCP::{1}. Returned varObj: {2}".format(newParamName, ECUname, varObj))
            return None

        if newObj.type == 0 or newObj.type == 1 or enableAll:
            parameter.AutoRead = 1
        else:
            self.log.warning("AutoRead disabled because of type!")
            parameter.AutoRead = 0

        self.log.debug("Enabled >>> %s" % parameter.Name)
        return True

    @func_wrapper
    def DisableXCPParam(self, ECU, paramName):
        """Disable single XCP parameter.

        :type ECU: McECU
        :param ECU: XCP ECU object

        :type paramName: string
        :param paramName: name of the XCP parameter
        """

        parameter = ECU.MeasurementGroups.Item(1).Parameters(paramName)

        parameter.AutoRead = 0
        parameter.Configured = 0

        self.log.debug("Disabled >>> %s" % parameter.Name)

    @func_wrapper
    def EnableXCPdata(self, xcpParamList, host='APH', mode='Poll'):
        """Enable XCP parameters on desired host.

        :type xcpParamList: string[]
        :param xcpParamList: list of XCP parameters

        :type host: string
        :param host: name of the host (Default value = 'APH')

        :type mode: string
        :param mode: read mode of the parameter ['Poll', 'DAQ']
        (Default value = 'Poll')

        .. note:: parameter host can have values [APH, SSH, SRH, APHFR]
        *APHFR = XCP over FlexRay on APH
        """

        notEnabledParams = self.CheckXCPParamList(xcpParamList, host, mode)

        if notEnabledParams is None:
            self.log.error("Could not enable specified parameters!")
            return None

        if len(notEnabledParams) <= 0:
            self.log.debug("All XCP parameters already enabled!")
            if self.IsECUActive(host):
                return True

        if self.isMeasurementRunning():
            self.StopMeasurement()
            time.sleep(2)

        self.ECUObj = self.GetAllECUs()

        self.log.debug("\nEnabling test points:")

        self.ActivateECUOnHost(host)

        for xcpParam in notEnabledParams:
            if self.EnableXCPParam(self.ECUObj[host], xcpParam, mode=mode) == None:
                return False

        if host in ['SSH', 'SRH']:
            if self.EnableXCPParam(self.ECUObj['APHFR'], self.SystemState, mode=mode) == None:
                return False

        return True

    @func_wrapper
    def CheckXCPParamList(self, xcpParamList, host='APH', mode='Poll'):
        notEnabledParams = []
        self.ECUObj = self.GetAllECUs()

        ECU = self.ECUObj[host]

        if host in ['APH', 'APHFR']:
            xcpParamList.append(self.SystemState)

        for xcpParam in xcpParamList:
            try:
                parameter = ECU.MeasurementGroups.Item(1).Parameters(xcpParam)
            except:
                self.log.error("Could not find specified parameter!")
                return None

            if parameter.Configured != 1:
                notEnabledParams.append(xcpParam)
            else:
                self.log.debug("Enabled >>> %s" % parameter.Name)

        return notEnabledParams

    @func_wrapper
    def SetXCPParamAutoRead(self, ECU, paramName, autoRead):
        """Set AutoRead option of XCP parameter.

        :type ECU: McECU
        :param ECU: XCP ECU object

        :type paramName: string
        :param paramName: name of the XCP parameter

        :type autoRead: bool
        :param autoRead: set AutoRead option of parameter
        """

        ECUname = ECU.Name
        # TODO Item(1)=BIST, counting through items and find specific
        try:
            parameter = ECU.MeasurementGroups.Item(1).Parameters(paramName)
        except:
            self.log.error("Could not find specified parameter!")
            return None

        if autoRead:
            parameter.AutoRead = 1
            self.log.info("Parameter %s AutoRead option set to True!" % paramName)
        else:
            parameter.AutoRead = 0
            self.log.info("Parameter %s AutoRead option set to False!" % paramName)

        return True

    @func_wrapper
    def SetTestPoint(self, testPoint, value, host='APH', retryLimit=10, withSleep=True):
        """Set value of test point.

        Try to set value of test point 10 times

        :type testPoint: string
        :param testPoint: name of the test point

        :type value: int, float...
        :param value: value on which test point will be set

        :type host: string
        :param host: name of the host (Default value = 'APH')

        :type withSleep: bool
        :param withSleep: wait between tries 0.5 seconds if True,
        don't wait if False (Default value = True)

        :type retryLimit: int
        :param retryLimit: number of retries to set testTpoint to
        value

        .. note:: parameter host can have values [APH, SSH, SRH, APHFR]
        *APHFR = XCP over FlexRay on APH
        """

        self.log.debug("Setting %s to %s..." % (testPoint, value))

        ns = self.XCPns[host]
        counter = 0
        while ((self.GetValueOfSysvar(testPoint, ns) != value) and
               (counter < retryLimit)):
            self.SetValueOfSysvar(value, testPoint, ns)
            counter += 1
            if withSleep:
                time.sleep(0.5)
        if counter >= retryLimit:
            self.log.error("Couldn't set %s to value %d in %d tries!"
                           % (testPoint, value, retryLimit))
            self.CheckXCPconnection(ns)
            return False
        return True

    @func_wrapper
    def ListAllECUs(self):
        """Print all XCP ECUs"""

        ECUs = self.CANoe.Configuration.GeneralSetup.XCPSetup.ECUs
        for i in range(ECUs.Count):
            self.log.debug("%s" % ECUs(i+1).Name)

    @func_wrapper
    def GetAllECUs(self):
        """Get all XCP ECUs.

        :return: dictionary of XCP ECU objects,
        key = host, value = XCP ECU object,
        None if object for desired host doesn't exist
        """

        ECUobjDict = {}
        for host in HOST_MAP:
            ECUobjDict[host] = self.SelectECU(XCPdevice[host])

        return ECUobjDict

    @func_wrapper
    def GetAllParams(self, ECUName):
        """Get all XCP parameters from XCP ECU object.

        :type ECUName: string
        :param ECUName: name of XCP ECU object

        :rtype: string[]
        :returns: list of all XCP parameters from desired XCP ECU object
        """

        paramList = []
        ECUs = self.CANoe.Configuration.GeneralSetup.XCPSetup.ECUs
        for i in range(ECUs.Count):
            Name = ECUs(i+1).Name
            if Name == ECUName:
                ECU = ECUs(i+1)
        Params = ECU.MeasurementGroups.Item(1).Parameters
        for i in range(Params.Count):
            # print Params.Item(i+1)
            param = Params.Item(i+1)
            # print param.Name
            paramList.append(param.Name)

        return paramList


class Power(object):
    def __init__():
        super(Power, self).__init__()
    
    @func_wrapper
    def EnableKL30(self):
        """Set KL30 to ON."""

        self.log.debug("Enabling KL30...\n")
        if not te_obj.globals['VTSystem']:
            objectKL30 = te_obj.util_functions['ux3_switch_handle']()
            if objectKL30:
                objectKL30.powerOn()
        return self.SetValueOfSysvar(1, "KL30", "HW_Access")

    @func_wrapper
    def DisableKL30(self):
        """Set KL30 to OFF."""

        self.log.debug("Disabling KL30...")
        if not te_obj.globals['VTSystem']:
            objectKL30 = te_obj.util_functions['ux3_switch_handle']()
            if objectKL30:
                objectKL30.powerOff()
        return self.SetValueOfSysvar(0, "KL30", "HW_Access")

    @func_wrapper
    def ResetSupply(self):
        """Reset power supply to 12 V."""

        self.DisableKL30()
        self.SetValueOfSysvar(12.0, "SetVoltage", "HW_Access")
        time.sleep(2)
        self.EnableKL30()

    @func_wrapper
    def CheckCurrent(self):
        """Check current of the board.

        :return: value of the current that board draws, 1 if CANoe VN
        configuration is used
        """

        if self.VNbox:
            self.log.warning("VN configuration is used, current by default 1A")
            return 1
        else:
            return self.GetValueOfSysvar("AvgCurrent", self.PowerModuleNS)

    @func_wrapper
    def CheckVoltage(self):
        """Check voltage of the board.

        :return: value of the voltage that board draws, 12 if CANoe VN
        configuration is used
        """

        if self.VNbox:
            self.log.warning("VN configuration is used, voltage by default 12V")
            return 12
        else:
            return self.GetValueOfSysvar("AvgVoltage", self.PowerModuleNS)


class CANoeAPI(Diag, XCP, Power):
    """CANoeAPI class."""
    def __init__(self):
        #super(CANoeAPI, self).__init__()
        """Creates variables associated with the class."""
        global te_obj
        te_obj = self.te_obj

        self.CANoe = None
        self.Config = None
        self.Measurement = None
        self.diagDev = None
        self.UART = None
        self.FlexRayNetwork = ""
        self.DiagNetwork = ""
        self.DiagDeviceName = ""
        self.SystemState = ""
        self.SystemStateVar = self.SystemState.replace(".", "_")
        self.PowerModuleNS = ""
        self.XCPns = None
        self.VNbox = False
        self.AppRunning = None
        self.myStream = None
        self.init_canoe_sem = False
        self.diagDev = None

        self.log = self.te_obj.log

        self.request = {'callback': None, 'response_ready': False, 'response_data': None, 'args': (), 'kwargs': {}}
        self.te_obj.start_thread('canoe_exe_thread', canoe_exe_thread)

    @func_wrapper
    def InitializeCOM(self):
        while(self.init_canoe_sem):
            time.sleep(0.5)

        self.init_canoe_sem = True
        self.CANoe = win32com.client.Dispatch("CANoe.Application")

        self.init_canoe_sem = False
        self.AppRunning = True
        return self.CANoe
        
    @func_wrapper
    def RunningApp(self):
        if self.AppRunning is None or self.AppRunning is False:
            self.AppRunning = len([p.name() for p in psutil.process_iter() if 'CANoe' in p.name()]) > 0
        return self.AppRunning

    @func_wrapper  
    def StartCANoe(self):
        """Start CANoe application.

        :returns: None if unable to run the CANoe application
        """
        global canoe
        return_value = None
        try:
            # starting CANoe
            if(not self.RunningApp()):
                self.log.debug("Starting Vector CANoe")
            self.InitializeCOM()
        except Exception as e:
            self.log.error("Could not start CANoe. Following error occurred: " + str(e))
            self.CANoe = None
            canoe = None
            return_value = False
        else:
            return_value = True
            canoe = self.CANoe
        return return_value

    @func_wrapper  
    def LoadCFG(self, cfg=""):
        """Load CANoe configuration.

        :type cfg: string
        :param cfg: Full path to CANoe .cfg file
        """
        return_value = False
        if(cfg != ""):
            te_obj.CANoe_configuration = cfg

        if "_VN" in te_obj.CANoe_configuration:
            self.VNbox = True

        if(te_obj.CANoe_configuration is not None):
            if(os.path.isfile(te_obj.CANoe_configuration)):
                if(te_obj.CANoe_configuration != self.CANoe.Configuration.FullName):
                    previous_state = self.isMeasurementRunning()
                    self.StopMeasurement()
                    
                    try:
                        self.CANoe.Open(te_obj.CANoe_configuration)
                        self.log.debug("Loading CANoe configuration: %s" % te_obj.CANoe_configuration)
                    except Exception as e:
                        self.log.warning("Cannot load configuration file: " + str(e))
                    else:
                        return_value = True
                        self.Config = te_obj.CANoe_configuration                    
                        if previous_state:
                            self.StartMeasurement()
                else:
                    te_obj.log.debug(te_obj.CANoe_configuration + " CANoe configuration already loaded")
            else:
                self.log.warning("CANoe CFG file does not exists!!!")
        return return_value

    @func_wrapper
    def ConfigFlexRayNetwork(self, networkName):
        """Set FlexRay network.

        :type networkName: string
        :param networkName: Name of the FlexRay network
        """

        self.log.debug("FlexRay network set to: %s" % networkName)
        self.FlexRayNetwork = networkName

    @func_wrapper
    def StartMeasurement(self, waitForState=0):
        """Start CANoe measurement.

        :type waitForState: int
        :param waitForState: Wait for specific state of the board when
        measurement is started (Default value = 0)
        """
        
        return_value = False
        self.Measurement = self.CANoe.Measurement
        netw = self.CANoe.Networks(self.DiagNetwork)
        self.diagDev = netw.Devices(self.DiagDeviceName).Diagnostic
        if self.isMeasurementRunning():
            self.log.debug("Measurement already running")
        else:
            try:
                self.Measurement.Start()
                self.log.debug("\nStarting CANoe measurement.\n")
            except:
                self.log.error("Could not start CANoe measurements")
            else:
                return_value = True

        if waitForState != 0:
            self.WaitUntilState(waitForState)
        return return_value

    @func_wrapper
    def isMeasurementRunning(self):
        """Checks if measurement is running.

        :return: True if measurement is running, False if not
        """

        return self.CANoe.Measurement.Running

    @func_wrapper
    def StopMeasurement(self):
        """Stop CANoe measurement."""

        self.Measurement = self.CANoe.Measurement
        if self.isMeasurementRunning():
            self.Measurement.Stop()
            self.log.debug("\nStoping CANoe measurement.\n")
        else:
            self.log.debug("\nCANoe Measurement already stopped.\n")

        time.sleep(5)

    @func_wrapper
    def SaveConfiguration(self):
        if (self.CANoe.Configuration.Saved == False):
            self.log.debug("Save CANoe measurement.\n")
            self.CANoe.Configuration.Save()



    @func_wrapper
    def ActivateSingleTest(self, TCname, WaitForFinish=False, TimeOut=20000):
        """Activation of CAPL test in CANoe.

        :type TCname: string
        :param TCname: name of the test

        :type WaitForFinish: bool
        :param WaitForFinish: wait for test to finish execution
        (default value = False)

        :type TimeOut: int
        :param TimeOut: maximum wait time in seconds (Default value = 20000)

        :return: value of verdict:
        1 for passed test,
        2 for failed test,
        other values for unexpected errors
        """

        verdict = None
        nodeFound = 0
        ProblematicTests = ""
        for env in range(1, int(self.CANoe.Configuration.TestSetup.TestEnvironments.Count) + 1):
            tstEnv = self.CANoe.Configuration.TestSetup.TestEnvironments.Item(env)
            tstCnt = tstEnv.Items.Count
            for j in range(tstCnt):
                selTest = tstEnv.Items(j+1)
                Name = selTest.Name
                if Name == TCname:
                    nodeFound = 1
                    SelectedTest = win32com.client.CastTo(selTest, "ITSTestModule")
                    if WaitForFinish:
                        unused_SelectedTest = win32com.client.DispatchWithEvents(
                                                SelectedTest,
                                                CANoeTestConfigurationEvents
                                                )

                        SelectedTest.Start()
                        # waiting for test to finish in CANoe
                        counter = 0
                        period = 0.1    # less than 1
                        ticks = TimeOut / period
                        while(ActiveTestingFlag is False and counter < ticks):
                            counter += 1
                            pythoncom.PumpWaitingMessages()
                            time.sleep(period)

                        if(ActiveTestingFlag is True):
                            verdict = SelectedTest.Verdict
                            if verdict == 1:
                                print "Test passed!"
                            elif verdict == 2:
                                print "Test failed!"
                            else:
                                print "End of test! Verdict not available!"
                    else:
                        SelectedTest.Start()

                    break
        if nodeFound == 0:
            ProblematicTests = ProblematicTests + TCname + ", "

        return verdict

    # single node NodeName status
    @func_wrapper
    def SingleNodeStatus(self, NodeName):
        """Status of node in CANoe.

        :type NodeName: string
        :param NodeName: name of the node

        :return: True if node is active, False if not, None if doesn't exist
        """

        nodeFound = False
        self.log.info("Status of %s node..." % NodeName)

        Nodes = self.CANoe.Configuration.SimulationSetup.Nodes
        for j in range(Nodes.Count):
            Name = Nodes.Item(j+1).Name

            if Name == NodeName:
                nodeFound = True
                Node = Nodes.Item(j+1)
                if Node.Active is True:
                    self.log.info("Node %s is active!" % NodeName)
                    return True
                else:
                    self.log.info("Node %s is NOT active!" % NodeName)
                    return False

        if not nodeFound:
            self.log.error("Did NOT found node %s" % NodeName)
            return None

    # activating single node NodeName
    @func_wrapper
    def ActivateSingleNode(self, NodeName):
        """Activation of node in CANoe.

        :type NodeName: string
        :param NodeName: name of the node
        """

        nodeFound = False
        self.log.info("Activation of %s node..." % NodeName)

        Nodes = self.CANoe.Configuration.SimulationSetup.Nodes
        for j in range(Nodes.Count):
            Name = Nodes.Item(j+1).Name

            if Name == NodeName:
                nodeFound = True
                Node = Nodes.Item(j+1)
                Node.Active = True
                self.log.info("Node %s activated!" % NodeName)
                break

        if not nodeFound:
            self.log.error("Did NOT found node %s" % NodeName)
        time.sleep(5)

    # deactivating single node NodeName
    @func_wrapper
    def DeactivateSingleNode(self, NodeName):
        """Deactivation of node in CANoe.

        :type NodeName: string
        :param NodeName: name of the node
        """

        nodeFound = False
        self.log.info("Deactivation of %s node..." % NodeName)

        Nodes = self.CANoe.Configuration.SimulationSetup.Nodes
        for j in range(Nodes.Count):
            Name = Nodes.Item(j+1).Name

            if Name == NodeName:
                nodeFound = True
                Node = Nodes.Item(j+1)
                Node.Active = False
                self.log.info("Node %s deactivated!" % NodeName)
                break

        if not nodeFound:
            self.log.error("Did NOT found node %s" % NodeName)
        time.sleep(5)

    @func_wrapper
    def SelectECU(self, ECUName):
        """Select desired XCP ECU.

        :type ECUName: string
        :param ECUName: name if XCP ECU object

        :return: XCP ECU object, None if object with desired name doesn't exist
        """

        ECUs = self.CANoe.Configuration.GeneralSetup.XCPSetup.ECUs
        for i in range(ECUs.Count):
            Name = ECUs(i+1).Name
            if Name == ECUName:
                ECU = ECUs(i+1)
                return ECU
        self.log.warning("ECU: %s does NOT exist!" % ECUName)
        return None

    @func_wrapper
    def WaitUntilXCPIsConnected(self, ECU, timeout=30):
        """Waits timeout seconds for ECU to connect via XCP.

        :type ECU: XCP ECU object
        :param ECU: XCP ECU which has to be connected via XCP

        :type timeout: int
        :param timeout: time in seconds for how long function will wait

        :return: True if ECU is connected via XCP, else False
        """

        start = time.time()
        while not ECU.Active:
            if time.time() - start > timeout:
                return False
        return True

    @func_wrapper
    def ActivateECU(self, ECU):
        """Activate desired XCP ECU object.

        :type ECU: McECU
        :param ECU: XCP ECU object
        """

        ECU.Active = 1
        ECU.ConnectOnMeasurementStart = 1
        ECU.DisconnectOnMeasurementStop = 1
        ECU.ObserverActive = 1
        # ECU.PageSwitchingActive = 1
        # ECU.RAMpage = 1
        ECU.ResetVariablesAfterDisconnect = 1

    @func_wrapper
    def DeactivateECU(self, ECU):
        """Deactivate desired XCP ECU object.

        :type ECU: McECU
        :param ECU: XCP ECU object
        """

        ECU.Active = 0
        ECU.ObserverActive = 0

    @func_wrapper
    def GetActiveECU(self, param=None):
        """Get currently active XCP ECU.

        :return: XCP ECU object, None if there is no active XCP ECUs
        """
        return_value = False
        ECUs = self.CANoe.Configuration.GeneralSetup.XCPSetup.ECUs
        for i in range(ECUs.Count):
            if ECUs(i+1).Active:
                self.log.debug("Active ECU: %s" % ECUs(i+1).Name)
                if param is not None:
                    return_value = getattr(ECUs(i+1), param)
                else:
                    return_value = ECUs(i+1)
                break
        if return_value is False:
            self.log.error("No active ECUs!")
        return return_value

    @func_wrapper
    def IsECUActive(self, host):
        """Check if XCP ECU is active for desired host.

        :type host: string
        :param host: name of the host

        .. note:: parameter host can have values [APH, SSH, SRH, APHFR]
        *APHFR = XCP over FlexRay on APH
        """

        ECUName = XCPdevice[host]

        ECUs = self.CANoe.Configuration.GeneralSetup.XCPSetup.ECUs
        for i in range(ECUs.Count):
            if ECUs(i+1).Active:
                if ECUs(i+1).Name == ECUName:
                    return True

        self.log.warning("ECU %s is NOT active!" % ECUName)
        return False

    @func_wrapper
    def GetECUseedNkey(self):
        activeECU = self.GetActiveECU()
        return activeECU.SeedAndKeyFileName

    @func_wrapper
    def SetECUseedNkey(self, ECUobj, seedNkey):
        ECUobj.SeedAndKeyFileName = seedNkey

    

    @func_wrapper 
    def GetSignalObj(self, busI, channel, msg, signalName):
        """Get signal object.

        :type busI: string
        :param busI: name of the bus

        :type channel: int
        :param channel: channel on which the signal is sent

        :type msg: string
        :param msg: name of the message to which the signal belongs

        :type signalName: string
        :param signalName: name of the signal

        :rtype: signal
        :returns: signal object, None if doesn't exist

        ..note:: channel can have values:
        1|cCAN
        2|cJ1939
        4|cTTP
        5|cLIN
        6|cMOST
        """

        buses = self.CANoe.Configuration.SimulationSetup.Buses
        bus = buses(busI)

        if bus is None:
            signal = None
        else:
            signal = bus.GetSignal(channel, msg, signalName)

        return signal

    @func_wrapper
    def getFRSignalValue(self, signalName, channel, msg):
        """Get value of FlexRay signal.

        :type signalName: string
        :param signalName: name of the signal

        :type channel: int
        :param channel: channel on which the signal is sent

        :type msg: string
        :param msg: name of the message to which the signal belongs

        :rtype: int, float...
        :returns: value of signal, None if doesn't exist

        ..note:: channel can have values:
        1|cCAN
        2|cJ1939
        4|cTTP
        5|cLIN
        6|cMOST
        """

        signal = self.GetSignalObj(self.FlexRayNetwork, channel, msg, signalName)

        if signal is not None:
            return signal.Value
        else:
            return None

    @func_wrapper
    def setFRSignalValue(self, signalValue, signalName, channel, msg, retryLimit=10, delay=0):
        """Set value of FlexRay signal.

        :type signalValue: int, float...
        :param signalValue: value on which signal will be set

        :type signalName: string
        :param signalName: name of the signal

        :type channel: int
        :param channel: channel on which the signal is sent

        :type msg: string
        :param msg: name of the message to which the signal belongs

        :type retryLimit: int
        :param retryLimit: number of retries to set signal to signalValue

        :rtype: int, float...
        :returns: value of signal, None if doesn't exist

        ..note:: channel can have values:
        1|cCAN
        2|cJ1939
        4|cTTP
        5|cLIN
        6|cMOST
        """
        for x in range(retryLimit):
            signal = self.GetSignalObj(self.FlexRayNetwork,
                                       channel,
                                       msg,
                                       signalName
                                       )
            if signal is not None:
                signal.Value = signalValue
            
            time.sleep(delay)
            
            if self.getFRSignalValue(signalName, channel, msg) == signalValue:
                return True

        return False

    @func_wrapper
    def getFRSignalState(self, signalName, channel, msg):
        """Get value of FlexRay signal.

        :type signalName: string
        :param signalName: name of the signal

        :type channel: int
        :param channel: channel on which the signal is sent

        :type msg: string
        :param msg: name of the message to which the signal belongs

        :rtype: int, float...
        :returns: state of signal, None if doesn't exist

        ..note:: channel can have values:
        1|cCAN
        2|cJ1939
        4|cTTP
        5|cLIN
        6|cMOST
        """

        signal = self.GetSignalObj(self.FlexRayNetwork, channel, msg, signalName)

        if signal is not None:
            return signal.State
        else:
            return None

    @func_wrapper 
    def GetFunction(self, funcName, params):
        """Get CANoe function.

        :type funcName: string
        :param funcName: name of the function

        :type params: int, float, string...
        :param params: parameters of the function

        ..warning:: This function is hard-coded currently!!!
        """

        # func = self.CANoe.CAPL.GetFunction("testWaitForFrPDU")
        global func
        result = func.Call("FD_ZFAS_Ch_A", 500)
        print result

    @func_wrapper 
    def GetNamespaceObj(self, nsName, thisNamespace=None, _level=0):
        """Get namespace object.

        Searches for namespace in whole namespace-tree

        :type nsName: string
        :param nsName: name of the namespace

        :type thisNamespave: namespace
        :param thisNamespace: namespace object (Default value = None)

        :type _level: int
        :param _level: level of depth in namespace-tree (Default value = 0)

        :rtype: namespace
        :returns: namespace object

        ..note:: nsName expected in format <lvl1>::<lvl2>...
        """

        lstNamespace = nsName.split('::')

        if _level >= len(lstNamespace):
            return thisNamespace

        # decide in which namespace-container to look
        if thisNamespace is None:
            objContainer = self.CANoe.System
        else:
            objContainer = thisNamespace

        for idxNs in range(1, objContainer.Namespaces.Count + 1):

            objNamespace = objContainer.Namespaces.Item(idxNs)
            if objNamespace.Name == lstNamespace[_level]:
                # namespace found, cast to datatype needed in order to use it
                foundNamespace = win32com.client.CastTo(objNamespace,
                                                        "INamespace3"
                                                        )

                return self.GetNamespaceObj(nsName,
                                            thisNamespace=foundNamespace,
                                            _level=_level + 1
                                            )
        return False

    # end def GetNamespaceObj
    @func_wrapper
    def GetVarsInNamespace(self, namespace):
        """Get all variables from one namespace.

        :type namespace: string
        :param namespace: name of the namespace

        :rtype: string[]
        :returns: list of all parameters from desired namespace

        ..note:: namespace expected in format <lvl1>::<lvl2>...
        """

        objNamespace = self.GetNamespaceObj(namespace)

        if objNamespace is not None:
            lstVarNames = []

            for idxVar in range(1, objNamespace.Variables.Count + 1):
                lstVarNames += [objNamespace.Variables.Item(idxVar).Name]

            return lstVarNames
        return None
    # end def GetVarsInNamespace

    @func_wrapper 
    def GetSysvarObj(self, varName, namespace=None):
        """Get system variable object.

        :type varName: string
        :param varName: name of the system variable

        :type namespace: string
        :param namespace: name of the namespace (Default value = None)

        :rtype: variable
        :returns: system variable object, None if doesn't exist

        .. note:: namespace expected in format <lvl1>::<lvl2>...
        """

        objNamespace = None

        if namespace is not None:
            objNamespace = self.GetNamespaceObj(namespace)
        else:
            objNamespace = self.CANoe.System

        if objNamespace is not False:
            try:
                for idxVar in range(1, objNamespace.Variables.Count + 1):
                    objSysvar = objNamespace.Variables.Item(idxVar)
                    if objSysvar.Name == varName:
                        return objSysvar
                
            except:
                self.log.error("Error in GetSysvarObj")
  
        return False
    # end def GetSysvarObj

    @func_wrapper
    def GetValueOfSysvar(self, varName, namespace=None):
        """Get value of system variable.

        :type varName: string
        :param varName: name of the system variable

        :type namespace: string
        :param namespace: name of the namespace (Default value = None)

        :rtype: int, float...
        :returns: value of system variable,
        False if system variable doesn't exist

        .. note:: namespace expected in format <lvl1>::<lvl2>...
        """
        #print "GetValueOfSysvar"
        objSysvar = self.GetSysvarObj(varName, namespace)

        if objSysvar is not False:
            return objSysvar.Value

        return objSysvar
    # end def GetValueOfSysvar

    @func_wrapper
    def SetValueOfSysvar(self, value, varName, namespace=None):
        """Set value of system variable.

        :type value: int, float...
        :param value: value on which system variable will be set

        :type varName: string
        :param varName: name of the system variable

        :type namespace: string
        :param namespace: name of the namespace (Default value = None)

        :rtype: int, float...
        :returns: False if value of system variable can't be set

        .. note:: namespace expected in format <lvl1>::<lvl2>...
        """
        #print "SetValueOfSysvar"
        objSysvar = self.GetSysvarObj(varName, namespace)
        #print "SetValueOfSysvar got GetSysvarObj"
        if objSysvar is None:
            return False

        try:
            objSysvar.Value = value
            return True
        except:
            self.log.debug("sysvar: {}::{} could not write value {}".format(namespace, varName, value))
            return False
    # end def SetValueOfSysvar

    @func_wrapper
    def SetValueOfSysvarList(self, index, value, varName, namespace=None, retryLimit = 10):
        """Set value of system variable list.

        :type index: int
        :param index: index of list that will be set

        :type value: int, float...
        :param value: value on which system variable will be set

        :type varName: string
        :param varName: name of the system variable

        :type namespace: string
        :param namespace: name of the namespace (Default value = None)

        :rtype: int, float...
        :returns: False if value of system variable can't be set

        .. note:: namespace expected in format <lvl1>::<lvl2>...
        """

        objSysvar = self.GetSysvarObj(varName, namespace)

        if objSysvar is None:
            return False

        originalValue = list(objSysvar.Value)
        originalValue[index] = value
        wantedValue = tuple(originalValue)

        try:
            counter = 0
            while ((self.GetValueOfSysvar(varName, namespace) != wantedValue) and
                   (counter < retryLimit)):
                objSysvar.Value = wantedValue
                counter += 1
                time.sleep(0.3)
            if counter >= retryLimit:
                self.log.error("Couldn't set %s[%d] to value %d in 10 tries!"
                               % (varName, index, value))
                self.CheckXCPconnection(namespace)
                return False
            return True

        except:
            self.log.debug("sysvar: {}::{} could not write value {}".format(namespace, varName, value))
            self.CheckXCPconnection(namespace)
            return False
    # end def SetValueOfSysvar

    @func_wrapper
    def GetValueOfEnvVar(self, varName):
        """Get value of environment variable.

        :type varName: string
        :param varName: name of the environment variable

        :rtype: int, float...
        :returns: value of environment variable,
        False if environment variable doesn't exist
        """

        objEnvVar = self.CANoe.Environment.GetVariable(varName)

        if objEnvVar is None:
            return False

        return objEnvVar.Value
    # end def GetValueOfEnvVar

    @func_wrapper
    def SetValueOfEnvVar(self, value, varName):
        """Set value of environment variable.

        :type value: int, float...
        :param value: value on which environment variable will be set

        :type varName: string
        :param varName: name of the environment variable

        :rtype: int, float...
        :returns: False if value of environment variable can't be set
        """

        objEnvVar = self.CANoe.Environment.GetVariable(varName)

        if objEnvVar is None:
            return False

        try:
            objEnvVar.Value = value
        except:
            self.log.debug("EnvVar: {} could not write value {}".format(varName, value))
    # end def SetValueOfEnvVar


    @func_wrapper
    def Quit(self):
        """ """

        self.CANoe.Quit()
        self.AppRunning = False


class CANoeTestConfigurationEvents(object):
    """ """

    def __init__(self):
        global ActiveTestingFlag
        ActiveTestingFlag = False

    def OnStart(self):
        """ """

        #print "event -> Start of testing..."

    def OnStop(self, App):
        """



        :param App:



        """

        global ActiveTestingFlag
        ActiveTestingFlag = True
        #print "event -> End of testing..."
