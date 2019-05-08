# -----------------------------------------------------------------------------
# # Copyright (C) 2013 TTTech Computertechnik AG. All rights reserved
# Schoenbrunnerstrasse 7, A--1040 Wien, Austria. office@tttech.com
#
# ++
# Name
#    CANoeAPI_zFAS
#
# Purpose
#    API for Vector CANoe (zFAS).
#
#
# Revision Dates
#      05-Apr-2018 eVTE: Creation. Implementation of CANoeAPI_zFAS class.
#
# Status: Development
# -----------------------------------------------------------------------------

import sys
import threading

import time
from Utils.CANoeAPI import CANoeAPI as CANoeAPI_base
from Utils.CANoeAPI_zFAS_series_Diag import Diagnostic as Diag

from Utils.test_config import STATES_MAP, XCPns, flashparams

RAW_DATA = [0x02, 0xD1, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF,
            0xFB, 0x00, 0x00, 0xF8, 0xFF, 0xFF, 0xDB, 0xFF, 0xD7, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xDF,
            0xFF, 0xBE, 0xBE, 0x7B, 0x7A, 0x00, 0x80, 0x00, 0x00, 0x00,
            0x80, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x00, 0x00, 0x80, 0x00,
            0x00, 0x00, 0x00, 0x00, 0xC0, 0x00, 0xFF, 0x00, 0x40, 0x00,
            0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x5F, 0xC8, 0x00, 0xA0,
            0x00, 0xD0, 0x00, 0x80, 0x00, 0x40, 0x00, 0x80, 0x00, 0x80,
            0x80, 0x80, 0xE0, 0x80, 0x80, 0xF0]


def func_wrapper(callback):
    def wrapper(self, *args, **kwargs):
        return_value = None
        if self.te_obj.threads['canoe_exe_thread']['Thread'] == threading.current_thread():
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


class CANoeAPI(CANoeAPI_base, Diag):
    """CANoeAPI_zFAS class."""
    def __init__(self, input_obj):
        """Creates variables associated with the class."""
        print "CANoe API zFAS"
        global te_obj
        te_obj = input_obj
        self.te_obj = input_obj
        super(CANoeAPI, self).__init__()
        
        self.FlexRayNetwork = "MLBevo_Fx_Cluster"
        self.DiagNetwork = self.FlexRayNetwork
        self.DiagDeviceName = "BV_FrontSensoDriveAssisSysteUDS"
        self.SystemState = "CtCdLCSM.PpPFProvidedData.DeLCSSystemState"
        self.SystemStateVar = self.SystemState.replace(".", "_")
        self.XCPns = XCPns
        self.PowerModuleNS = "VTS::M_PWR_ECU_KL30_PWR"
    
    @func_wrapper
    def ConfigFlexRayNetwork(self, networkName):
        """Set FlexRay network.

        :type networkName: string
        :param networkName: Name of the FlexRay network
        """

        self.log.debug("FlexRay network set to: %s" % networkName)
        self.FlexRayNetwork = networkName
        self.DiagNetwork = networkName

    @func_wrapper
    def EnableSystemState(self):
        """Enable XCP variable DeLCSSystemState for monitoring."""

        self.EnableXCPdata([])

    @func_wrapper
    def GetSystemState(self):
        """Get value of XCP variable DeLCSSystemState.

        :return: Value of the variable DeLCSSystemState
        """

        state = self.GetValueOfSysvar(self.SystemStateVar, self.XCPns['APH'])
        if state:
            return state
        else:
            return self.GetValueOfSysvar(self.SystemStateVar,
                                         self.XCPns['APHFR'])

    @func_wrapper
    def EnableFR(self):
        """Enable FlexRay communication."""

        self.log.debug("Enabling FlexRay...")
        # self.SetValueOfEnvVar(1, "EnvKlemme15")
        # self.SetValueOfSysvar(1, "Set_KL15_SW", "PDU_Mod")
        self.SetValueOfSysvar(1, "Ignition", "IL_FR1")

    @func_wrapper
    def DisableFR(self):
        """Disable FlexRay communication."""

        self.log.debug("Disabling FlexRay...")
        # self.SetValueOfEnvVar(0, "EnvKlemme15")
        # self.SetValueOfSysvar(0, "Set_KL15_SW", "PDU_Mod")
        self.SetValueOfSysvar(0, "Ignition", "IL_FR1")

    @func_wrapper
    def CheckFR(self):
        """Checks FlexRay communication state.

        :return: True if FlexRay communication is on, False if not
        """

        KL15 = self.GetValueOfSysvar("Set_KL15_SW", "PDU_Mod")
        FR = self.GetValueOfEnvVar("EnvKlemme15")
        if KL15 and FR:
            return True
        else:
            return False

    @func_wrapper
    def RestartBoard(self, timeout=30, waitForRunning=True):
        """Restart the board, reset voltage to 12 V and reset
        FlaxRay communication if turned off, then wait for Running state if
        parameter is True, otherwise sleep for value of timeout.

        :type timeout: int
        :param timeout: time in seconds (Default value = 30)

        :type waitForRunning: bool
        :param waitForRunning: wait for Running state of the board
        (Default value = True)
        """

        if self.VNbox:
            if not self.CheckFR():
                self.EnableFR()
            self.SendDiagRequestKeyOffOnReset()
        else:
            self.DisableKL30()
            self.SetValueOfSysvar(12.0, "SetVoltage", "HW_Access")
            if not self.CheckFR():
                self.EnableFR()
            time.sleep(2)
            self.EnableKL30()
            self.log.debug("Voltage value currently: %f" % self.CheckVoltage())
        if waitForRunning:
            self.WaitUntilState()
        else:
            time.sleep(timeout)
            
        return True
            

    @func_wrapper
    def ProperShutdown(self):
        """Execute proper shutdown.
        Reset voltage to 12 V, clear DTCs then disable FlexRay communication
        for board to power off, enable FlexRay again and wait for
        Running state.

        :return: True if everything was ok, False if not
        """

        self.log.debug("Proper shutdown...")
        if int(self.GetValueOfSysvar("SetVoltage", "HW_Access")) != 12:
            self.SetValueOfSysvar(12.0, "SetVoltage", "HW_Access")

        if self.CheckFR() and self.GetSystemState() == 4:
            time.sleep(5)
            cnt = 0
            while (not self.ClearDiagnosticInformation() and cnt < 10):
                time.sleep(1)
                cnt += 1
        else:
            self.EnableFR()
            time.sleep(5)
            cnt = 0
            while (not self.ClearDiagnosticInformation() and cnt < 10):
                time.sleep(1)
                cnt += 1

        cnt = 0
        while(cnt < 5):
            self.DisableFR()
            if self.WaitUntilState(6, timeout=60):
                if self.WaitUntilState(1):
                    time.sleep(1)
                    self.EnableFR()
                    if self.WaitUntilState():
                        return True
            cnt += 1

        self.RestartBoard()
        return False

    @func_wrapper
    def WaitUntilState(self, state=4, step=1, timeout=30, retTime=False):
        """Wait for specific board state.

        :type state: int
        :param state: desired state, 1 is used for waiting for board to
        power off and other values for waiting specific states
        (APH XCP over Eth or FR needed) (Default value = 4)

        :type step: int, float
        :param step: interval in seconds in which state of the board is checked
         (Default value = 1)

        :type timeout: int
        :param timeout: maximum wait time in seconds (Default value = 30)

        :type retTime: bool
        :param retTime: function will return time passed (in seconds) to reach
        desired state if parameter is True, otherwise bool is returned
        (Default value = False)

        :return: depending of parameter retTime, return value is:
        time passed (in seconds) in which desired state is reached when retTime is True,
        bool value (which indicates if desired state is reached) when retTime is False
        """

        start = time.time()
        te_obj.monitor.add_condition('APH', 'Start power-off sequence')
        if state == 1:
            if self.VNbox:
                self.log.warning("VN configuration is used, checking UART instead of current!")
                if te_obj.monitor is not None:
                    found = te_obj.monitor.check_condition('APH', 'Start power-off sequence', timeout)
                    te_obj.monitor.reset_condition('APH', 'Start power-off sequence')
                    if found:
                        self.log.info("\nBoard Restarted!")
                        return True
                    else:
                        self.log.info("\nTimeout!")
                        return False

                else:
                    self.log.warning("UART is not available to CANoe!")
                    self.log.warning("Waiting for %d seconds..." % timeout)
                    time.sleep(timeout)
            else:
                while(True):
                    elipsedTime = time.time() - start
                    if retTime:
                        sys.stdout.write("\rWaiting... %f seconds" % elipsedTime)
                    currCurrent = self.CheckCurrent()
                    if currCurrent < 1.0:
                        self.log.info("\nBoard Powered Off!")
                        if retTime:
                            self.log.info("Waited = %f seconds" % elipsedTime)
                            return elipsedTime
                        else:
                            return True
                    elif int(elipsedTime) > timeout:
                        self.log.info("\nTimeout!")
                        if retTime:
                            return elipsedTime
                        else:
                            return False

                    time.sleep(step)
        else:
            activeECU = self.GetActiveECU('Name')
            if activeECU is not False:
                if 'ApplicationHost' not in activeECU:
                    if not self.IsECUActive("APHFR"):
                        self.log.warning("Active ECU is not APH, "
                                         "waiting by default 30 seconds...")
                        time.sleep(30)
                        return
            else:
                self.log.warning("There is NO active ECU's, "
                                 "waiting by default 30 seconds...")
                time.sleep(30)
                return
            while(True):
                elipsedTime = time.time() - start
                if retTime:
                    sys.stdout.write("\rWaiting... %f seconds" % elipsedTime)
                SystemState = self.GetSystemState()

                if SystemState == state:
                    self.log.debug("\nCorrect system state (%s)!\n"
                                  % STATES_MAP[state])
                    if state == 4:
                        time.sleep(10)
                    if retTime:
                        self.log.debug("Waited = %f seconds!" % elipsedTime)
                        return elipsedTime
                    else:
                        return True
                else:
                    currCurrent = self.CheckCurrent()
                    if currCurrent < 1.0 and int(elipsedTime) > timeout:
                        self.log.debug("\nBoard Powered Off!")
                        if retTime:
                            self.log.debug("Waited = %f seconds!" % elipsedTime)
                            return elipsedTime
                        else:
                            return False
                    elif int(elipsedTime) > timeout:
                        self.log.debug("\nTimeout!")
                        if isinstance(SystemState, (int, long)):
                            self.log.debug("Incorrect system state (%s)!\n"
                                           % STATES_MAP[SystemState])
                            if state != 5 and SystemState == 5:
                                self.DisableFR()
                                time.sleep(2)
                                self.EnableFR()
                                time.sleep(10)
                        else:
                            self.log.error("Unknown system state")
                        if retTime:
                            return elipsedTime
                        else:
                            return False

                time.sleep(step)

    @func_wrapper
    def SendDiagRequestWriteInitialIdentification(self, allZero=False):
        """Write initial identification.

        -Initialize diagnostics,
        -go to development session,
        -create request and set parameters,
        -check if positive response is received

        :rtype: bool
        :returns: True if diagnostic response is positive, False if not
        """

        diagDev = self.InitDiagnostic()

        self.SendDiagRequestDiagnosticSession("development")

        diagReq = diagDev.CreateRequest("DiagnServi_WriteDataByIdentECUIdent")

        diagReq.SetParameter("Param_RecorDataIdent", 0xF198)

        if not allZero:
            diagReq.SetParameter("Param_ImporNumbe", [0x03, 0xFF])
            diagReq.SetParameter("Param_VWDevicNumbe", [0x1F, 0xFF, 0xFF])
            diagReq.SetParameter("Param_WorksNumbe", [0x01, 0xFF, 0xFF])

        resp = self.SendRequestWaitResponse(diagReq)
        if (self.CheckResponse(resp)):
            self.log.debug("Initial identification!")
            return True
        else:
            return False

    @func_wrapper
    def SendDiagRequestHILmode(self, activate=True):
        """Activate or deactivate HIL mode.

        -Initialize diagnostics,
        -create request and set parameters,
        -check if request is fullfiled

        :type activate: bool
        :param activate: Activate or deactivate HIL mode (Default value = True)

        :rtype: bool
        :returns: True if request is fullfiled, False if not
        """

        diagDev = self.InitDiagnostic()

        diagReq = diagDev.CreateRequest("DiagnServi_WriteDataByIdentECUIdent")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Repair Shop Code Or Tester Serial Number")

        self.log.debug("Sending Repair Shop Code Or Tester Serial Number...")
        resp = self.SendRequestWaitResponse(diagReq)

        if (self.CheckResponse(resp)):
            diagReq = diagDev.CreateRequest("DiagnServi_WriteDataByIdentCalibData")

            diagReq.SetParameter("Param_RecorDataIdent",
                                 "Platform_zFAS_hil_mode")
            if activate:
                diagReq.SetParameter("Param_HilMode",
                                     "active")
                self.log.debug("Setting HIL mode to active...")
            else:
                diagReq.SetParameter("Param_HilMode",
                                     "not_active")
                self.log.debug("Setting HIL mode to not_active...")

            resp = self.SendRequestWaitResponse(diagReq)

            if (self.CheckResponse(resp)):
                if activate:
                    self.log.debug("HIL mode active!")
                else:
                    self.log.debug("HIL mode not_active!")
                return True
            else:
                return False

    @func_wrapper
    def SendDiagRequestGetSecurityAccess(self):
        """Get security access.

        -Initialize diagnostics,
        -go to development session,
        -request seed login,
        -ask for security access,
        -check if security access is granted

        :rtype: bool
        :returns: True if security access is granted, False if not
        """

        diagDev = self.InitDiagnostic()

        self.SendDiagRequestDiagnosticSession("development")

        diagReq = diagDev.CreateRequest("DiagnServi_SecurAccesRequeSeedLogin")

        resp = self.SendRequestWaitResponse(diagReq)

        if (self.CheckResponse(resp)):
            seed = resp.GetParameter("Param_SecurAccesSeed")
            self.log.debug("Access seed: %s" % str(seed))
        else:
            seed = 0

        if seed:
            self.log.debug("Adding PIN on seed..")
            key = hex(int(seed, 16) + int('0x4E87', 16))
            if len(key) == 11:
                key = key[:-1]
            self.log.debug("New key: " + key)
            diagReq = diagDev.CreateRequest("DiagnServi_SecurAccesSendKeyLogin")
            diagReq.SetParameter("Param_SecurAccesKey", key)
            time.sleep(2)
            resp = self.SendRequestWaitResponse(diagReq)

            if (self.CheckResponse(resp)):
                self.log.debug("Security access granted!")
                return True
            else:
                return False

    @func_wrapper
    def SendDiagRequestWriteCodingData(self, allZero=False):
        """Write coding data.

        -Initialize diagnostics,
        -create request and set parameters (RAW_DATA),
        -check if positive response is received

        :rtype: bool
        :returns: True if diagnostic response is positive, False if not
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_WriteDataByIdentVariaCodinTextu")

        if not allZero:
            diagReq.SetParameter("Param_RawData", RAW_DATA)

        resp = self.SendRequestWaitResponse(diagReq)

        if (self.CheckResponse(resp)):
            self.log.debug("Writing of raw data was successful!")
            return True
        else:
            self.log.error("Writing of raw data was unsuccessful!")
            return False

    @func_wrapper
    def SendDiagRequestReadCodingData(self):
        """Read coding data.

        -Initialize diagnostics,
        -create request and set parameters,
        -check if read data is same as RAW_DATA

        :rtype: bool
        :returns: True if read data is same as RAW_DATA,
        False if not or response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentVariaCodin")

        resp = self.SendRequestWaitResponse(diagReq)

        if (self.CheckResponse(resp)):
            self.log.debug("Reading of raw data was successful!")
            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(hex(ord(c)))

            #===================================================================
            # del responseRaw[2]
            # del responseRaw[1]
            # del responseRaw[0]
            #===================================================================

            notTheSame = False
            if len(responseRaw) == len(RAW_DATA):
                for i in range(len(RAW_DATA)):
                    print hex(RAW_DATA[i]), responseRaw[i]

                    if hex(RAW_DATA[i]) != responseRaw[i]:
                        notTheSame = True
                        break
            else:
                self.log.debug("Not the same length!")

            if notTheSame:
                self.log.error("Not the same as RAW_DATA")
                return False
            else:
                self.log.debug("Data are the same!")
                return True
        else:
            self.log.error("Reading of raw data was unsuccessful!")
            return False

    @func_wrapper
    def SendDiagRequestTemperature(self, qualif=True):
        """Get temperatures and qualifiers (optional) from all hosts.

        -Initialize diagnostics,
        -create request and set parameters,
        -get all parameters if positive response is received

        :type qualif: bool
        :param qualif: Get all qualifiers with temperatures (Default value = True)

        :rtype: string[]
        :returns: list of all temperatures and qualifiers (optional),
        None if response is negative

        ..note:: Temperatures are returned in order -> AVG, PCB, APH, SSH, SRH
        same order is for qualifiers
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "zFAS_Plattform_Control modul_temperature_dev")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp):
            AVEtemp = resp.GetParameter("Param_TestProgrAveraTempe")
            PCBtemp = resp.GetParameter("Param_TestProgrPrintCircuBoard")
            APHtemp = resp.GetParameter("Param_TestProgrAppliHost")
            SSHtemp = resp.GetParameter("Param_TestProgrSensoSysteHost")
            SRHtemp = resp.GetParameter("Param_TestProgrSensoRecogHost")
            AVETempQualif = resp.GetParameter("Param_QualiTempeAvera")
            PCBTempQualif = resp.GetParameter("Param_QualiTempePCB")
            APHTempQualif = resp.GetParameter("Param_QualiTempeAPH")
            SSHTempQualif = resp.GetParameter("Param_QualiTempeSSH")
            SRHTempQualif = resp.GetParameter("Param_QualiTempeSRH")

            if qualif:
                return [AVEtemp, PCBtemp, APHtemp, SSHtemp, SRHtemp,
                        AVETempQualif, PCBTempQualif,
                        APHTempQualif, SSHTempQualif, SRHTempQualif]
            else:
                return [AVEtemp, PCBtemp, APHtemp, SSHtemp, SRHtemp]
        else:
            return None

    @func_wrapper
    def SendDiagRequestTemperatureStatus(self):
        """Get temperature status.

        -Initialize diagnostics,
        -create request and set parameters,
        -get temperature status if positive response is received

        :rtype: int
        :returns: temperature status, None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Temperature_status")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            TemperatureStatusStr = resp.GetParameter("Param_TempeStatu")
            if 'not_available' in TemperatureStatusStr:
                TemperatureStatus = 0
            else:
                TemperatureStatus = int(TemperatureStatusStr[-1:])
            return TemperatureStatus
        else:
            return None

    @func_wrapper
    def SendDiagRequestErrorHandler(self, host='APH'):
        """Get Error Handler circular buffer.

        Get the complete Messwert Status (circular buffer with qualified errors)
        from a specified host, which is available on APH, SSH and SRH.

        :type host: string
        :param host: Name of the host (Default value = 'APH')

        :rtype: string[]
        :returns: circular buffer  with qualified errors,
        None if response is negative

        ..note:: parameter host can have values [APH, SSH, SRH]
        """
        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")
        hostsAndParams = {'APH': 'Platform_zFAS_Error_Handler_Master',
                          'SSH': 'Platform_zFAS_Error_Handler_SSH',
                          'SRH': 'Platform_zFAS_Error_Handler_SRH'}

        diagReq.SetParameter("Param_RecorDataIdent",
                             hostsAndParams[host])
        resp = self.SendRequestWaitResponse(diagReq)
        self.log.debug("Reading of raw data was successful!")
        responseRaw = []
        if self.CheckResponse(resp):
            # ErrorHandlerArr = resp.GetParameter("Param_Error")
            ErrorHandlerArr = resp.Stream
            for c in ErrorHandlerArr:
                responseRaw.append(hex(ord(c)))
            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw
        else:
            return None

    @func_wrapper
    def SendDiagRequestResetReason(self, host='APH'):
        """Get reset reason value.

        :type host: string
        :param host: Name of the host (Default value = 'APH')

        :rtype: string[]
        :returns: XXX

        ..note:: parameter host can have values [APH, SSH, SRH]
        """
        if self.SendDiagRequestDiagnosticSession("development"):
            diagDev = self.InitDiagnostic()
            diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

            hostsAndParams = {'APH': 'Platform_zFAS_ResetReason',
                              'SSH': 'Platform_zFAS_ResetReason',
                              'SRH': 'Platform_zFAS_ResetReason'}

            diagReq.SetParameter("Param_RecorDataIdent",
                                 hostsAndParams[host])

            resp = self.SendRequestWaitResponse(diagReq)
            self.log.info("Reading of raw data was successful!")
            if self.CheckResponse(resp):
                rstRsn = int(resp.GetParameter("Param_LastResetReaso"))
            else:
                rstRsn = None

        return rstRsn

    @func_wrapper
    def SendDiagRequestNoOfECUResets(self):
        """Get number of ECU resets.

        -Initialize diagnostics,
        -create request and set parameters,
        -get number of ECU resets if positive response is received

        :rtype: int
        :returns: number of ECU resets, None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Number of ECU Resets")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            CurreDriviCycleCountStr =\
                resp.GetParameter("Param_CurreDriviCycleCount")
            CurreDriviCycleCount = int(CurreDriviCycleCountStr)
            return CurreDriviCycleCount
        else:
            return None

    @func_wrapper
    def SendDiagRequestInternalHostState(self, log=True):
        """Get LCS states from all hosts.

        -Initialize diagnostics,
        -create request and set parameters,
        -get all parameters if positive response is received

        :type log: bool
        :param log: Write response status (Default value = True)

        :rtype: string[]
        :returns: list of all LCS host states, None if response is negative

        ..note:: LCS host states are returned in order
        -> Sys, APH, SSH, SRH, MVH
        """

        diagDev = self.InitDiagnostic(log)
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_Internal_Host_State")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp, log):
            SYSStatus = resp.GetParameter("Param_SysteStatu")
            APHStatus = resp.GetParameter("Param_APHStatu")
            SSHStatus = resp.GetParameter("Param_SSHStatu")
            SRHStatus = resp.GetParameter("Param_SRHStatu")
            MVHStatus = resp.GetParameter("Param_MVHStatu")

            return [SYSStatus, APHStatus, SSHStatus, SRHStatus, MVHStatus]
        else:
            return None

    @func_wrapper
    def SendDiagRequestWatchdogSSH(self, log=True):
        """Get Watchdog SSH status.

        -Initialize diagnostics,
        -create request and set parameters,
        -get Watchdog SSH status if positive response is received

        :type log: bool
        :param log: Write response status (Default value = True)

        :rtype: string
        :returns: Watchdog SSH status, None if response is negative
        """

        diagReq = self.diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "zFAS_Plattform_Watchdog_SSH")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp, log):
            diagRespToReturn = dict()
            diagRespToReturn['Param_SSHAnswe'] = resp.GetParameter("Param_SSHAnswe")
            diagRespToReturn['Param_SSHErrCount'] = resp.GetParameter("Param_SSHErrCount")

            return diagRespToReturn
        else:
            return None

    @func_wrapper
    def SendDiagRequestWatchdogAPH(self, log=True):
        """Get Watchdog APH status.

        -Initialize diagnostics,
        -create request and set parameters,
        -get Watchdog APH status if positive response is received

        :type log: bool
        :param log: Write response status (Default value = True)

        :rtype: string
        :returns: Watchdog APH status, None if response is negative
        """

        diagReq = self.diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "zFAS_Plattform_Watchdog_APH")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp, log):
            HSVMAnsw = resp.GetParameter("Param_WdgMERSEID")

            return HSVMAnsw
        else:
            return None

    @func_wrapper
    def SendDiagRequestTegraPowerSupply(self, log=True):
        """Get Tegra power supply value.

        -Initialize diagnostics,
        -create request and set parameters,
        -get Tegra K1 Power Supply if positive response is received

        :type log: bool
        :param log: Write response status (Default value = True)

        :rtype: string
        :returns: Value of Tegra K1 Power Supply, None if response is negative
        """

        diagDev = self.InitDiagnostic(log)
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_Tegra_K1_Power_Supply")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp, log):
            return resp.GetParameter("__SwitchKey__")
        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SMU_Errors(self):
        """Get count of all SMU errors.

        -Initialize diagnostics,
        -create request and set parameters,
        -get count of all SMU errors if positive response is received

        :rtype: string
        :returns: Count of all SMU errors, None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SMU_Errors")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            count = resp.GetParameter("Param_SMUFaultCount")
            return count
        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_PCI_Connenction_Status(self):
        """Get raw response of PCI connection status.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of PCI connection status if positive response is
        received

        :rtype: string[]
        :returns: Raw response of PCI connection status,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SRH_PCIe_Connenction_Status")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw
        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_I2C_Connenction_Status(self):
        """Get raw response of I2C connection status.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of I2C connection status if positive response is
        received

        :rtype: string[]
        :returns: Raw response of I2C connection status,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SRH_I2C_Connenction_Status")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw
        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SRH_Source_of_Last(self):
        """Get raw response of SRH source of last.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SRH source of last if positive response is
        received

        :rtype: string[]
        :returns: Raw response of SRH source of last,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SRH_Source_of_Last")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw
        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SSH_CPU_faults(self):
        """Get raw response of SSH CPU faults.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SSH CPU faults if positive response is received

        :rtype: string[]
        :returns: Raw response of SSH CPU faults, None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SSH_CPU_faults")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw
            """
            return [resp.GetParameter("Param_DetaiErrorCodeForStartError0"),
                    resp.GetParameter("Param_DetaiErrorCodeForStartError1"),
                    resp.GetParameter("Param_ErrorIDForDetaiErrorCodeForStartError0"),
                    resp.GetParameter("Param_ErrorIDForDetaiErrorCodeForStartError1")
                    ]
            """
        else:
            return None

    @func_wrapper
    def SendDiagRequestNumberOfECUResets(self):
        """Get raw response of Number of ECU resets.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of Number of ECU resets if positive response is received

        :rtype: string[]
        :returns: Raw response of Number of ECU resets, None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             0x0401)

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw
            """
            return [resp.GetParameter("Param_DetaiErrorCodeForStartError0"),
                    resp.GetParameter("Param_DetaiErrorCodeForStartError1"),
                    resp.GetParameter("Param_ErrorIDForDetaiErrorCodeForStartError0"),
                    resp.GetParameter("Param_ErrorIDForDetaiErrorCodeForStartError1")
                    ]
            """
        else:
            return None

    # returns RAW data
    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SSH_DD3_RAM_Faults(self):
        """Get raw response of SSH DD3 RAM faults.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SSH DD3 RAM faults if positive response is
        received

        :rtype: string[]
        :returns: Raw response of SSH DD3 RAM faults,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SSH_DD3_RAM_Faults")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):

            """
            print resp.GetParameter("Param_MemorAddre1RegisTextu")
            print resp.GetParameter("Param_MemorAddre1Value")
            print resp.GetParameter("Param_MemorAddre2RegisTextu")
            print resp.GetParameter("Param_MemorAddre2Value")
            print resp.GetParameter("Param_MemorAddre3RegisTextu")
            print resp.GetParameter("Param_MemorAddre3Value")
            print resp.GetParameter("Param_MemorAddre4RegisTextu")
            print resp.GetParameter("Param_MemorAddre4Value")
            print resp.GetParameter("Param_MemorAddre5RegisTextu")
            print resp.GetParameter("Param_MemorAddre5Value")
            """

            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw

        else:
            return None

    # returns RAW data
    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SSH_Memory_Health_2(self):
        """Get raw response of SSH memory health 2.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SSH memory health 2 if positive response is
        received

        :rtype: string[]
        :returns: Raw response of SSH memory health 2,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SSH_Memory_Health_2")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw
            # return [resp.GetParameter("Param_ECCErrorSDRAMContrTextu")]
        else:
            return None

    # returns RAW data
    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SSH_Test_Register_Results(self):
        """Get raw response of SSH test register results.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SSH test register results if positive response is
        received

        :rtype: string[]
        :returns: Raw response of SSH test register results,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SSH_Test_Register_Results")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):

            """
            print resp.GetParameter("Param_SafetRelevRegis1IDTextu")
            print resp.GetParameter("Param_SafetRelevRegis1Value")
            print resp.GetParameter("Param_SafetRelevRegis2IDTextu")
            print resp.GetParameter("Param_SafetRelevRegis2Value")
            print resp.GetParameter("Param_SafetRelevRegis3IDTextu")
            print resp.GetParameter("Param_SafetRelevRegis3Value")
            print resp.GetParameter("Param_SafetRelevRegis4IDTextu")
            print resp.GetParameter("Param_SafetRelevRegis4Value")
            print resp.GetParameter("Param_SafetRelevRegis5IDTextu")
            print resp.GetParameter("Param_SafetRelevRegis5Value")
            """

            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw

        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SSH_Source_of_Last_Reset(self):
        """Get raw response of SSH source of last reset.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SSH source of last reset if positive response is
        received

        :rtype: string[]
        :returns: Raw response of SSH source of last reset,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SSH_Source_of_Last_Reset")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):

            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            # return resp.GetParameter("Param_SSHSourcOfLastReset")

            return [''.join(responseRaw)]

        else:
            return None

    @func_wrapper
    def SendDiagRequestReadPersistencyData(self, host):
        """Get raw response of persistancy data for desired host.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of persistancy data for desired host if positive
        response is received

        :type host: string
        :param host: Name of the host (Default value = 'APH')

        :rtype: string[]
        :returns: Raw response of persistancy data for desired host,
        None if response is negative

        ..note:: parameter host can have values [APH, SSH, SRH]
        """

        diagDev = self.InitDiagnostic()
        hostsAndParams = {'APH': 'Platform_zFAS_Persistency_Status_APH',
                          'SSH': 'Platform_zFAS_Persistency_Status_SSH',
                          'SRH': 'Platform_zFAS_Persistency_Status_SRH'}

        self.SendDiagRequestDiagnosticSession("development")
        self.SendDiagRequestGetSecurityAccess()
        diagReq = diagDev.CreateRequest("DiagnServi_RoutiContrStartBasicSetti")
        diagReq.SetParameter("Param_RoutiIdent", 0x1001)
        resp = self.SendRequestWaitResponse(diagReq)

        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")
        diagReq.SetParameter("Param_RecorDataIdent",
                             hostsAndParams[host])
        resp = self.SendRequestWaitResponse(diagReq)
        self.log.debug("Reading of raw data was successful!")
        if self.CheckResponse(resp):

            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c)))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw  # [''.join(responseRaw[0:4]), ''.join(responseRaw[4:8])]

        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_Recorder_APH(self):
        """Get raw response of SSH DD3 RAM faults.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SSH DD3 RAM faults if positive response is received

        :rtype: string[]
        :returns: Raw response of SSH DD3 RAM faults,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        rawDataRecord = []

        for x in range(0, 8):
            print "Iteration: " + str(x)
            self.SendDiagRequestDiagnosticSession("development")
            self.SendDiagRequestGetSecurityAccess()
            diagReq = diagDev.CreateRequest("DiagnServi_RoutiContrStartBasicSetti")
            diagReq.SetParameter("Param_RoutiIdent", 0x1001)
            resp = self.SendRequestWaitResponse(diagReq)

            diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")
            diagReq.SetParameter("Param_RecorDataIdent", "Platform_zFAS_Recorder_APH")
            resp = self.SendRequestWaitResponse(diagReq)

            if self.CheckResponse(resp):
                responseRaw = []
                stream = resp.Stream
                for c in stream:
                    responseRaw.append(ord(c))

                del responseRaw[2]
                del responseRaw[1]
                del responseRaw[0]

                rawDataRecord.extend(responseRaw)
            else:
                print "Something went wrong with zFAS. Please repeat the execution."
                return None

        print "zFAS Recorder raw data is ready."
        return rawDataRecord

        # Example of usage:
        # filename = 'recorder.txt'
        # f = open(filename, 'w')
        # rawDataRecord = []

        # recorderData = CANoe.SendDiagRequestPlatform_zFAS_Recorder_APH()

        # if recorderData != None:
            # for x in recorderData:
                # f.write(': ' + str(x) + ';' + str(x) + '\n')  # python will convert \n to os.linesep
        # f.close()
        # os.rename(filename, filename[:-4] + '.par')
        # print "zFAS Recorder file is ready."

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_Recorder_APH_New(self):
        """Get raw response of SSH DD3 RAM faults.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of zFAS_Recorder_APH values if positive response is received for versions of x275 and higher

        :rtype: string[]
        :returns: Raw response of zFAS_Recorder_APH values for versions of x275 and higher,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        rawDataRecord = []
        for x in range(0, 9):
            print "Iteration: " + str(x)
            self.SendDiagRequestDiagnosticSession("development")
            self.SendDiagRequestGetSecurityAccess()
            time.sleep(2)
            diagReq = diagDev.CreateRequest("DiagnServi_RoutiContrStartBasicSetti")
            diagReq.SetParameter("Param_RoutiIdent", 0x1001)
            resp = self.SendRequestWaitResponse(diagReq)
            time.sleep(2)
            diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")
            diagReq.SetParameter("Param_RecorDataIdent", "Platform_zFAS_Recorder_APH")
            resp = self.SendRequestWaitResponse(diagReq)
            time.sleep(2)
            if self.CheckResponse(resp):
                if x > 0:
                    responseRaw = []
                    stream = resp.Stream
                    for c in stream:
                        responseRaw.append(ord(c))

                    del responseRaw[2]
                    del responseRaw[1]
                    del responseRaw[0]

                    rawDataRecord.extend(responseRaw)
                else:
                    pass
            else:
                print "Something went wrong with zFAS. Please repeat the execution."
                return None
        print "zFAS Recorder raw data is ready."
        return rawDataRecord

        # Example of usage:
        # filename = 'recorder.txt'
        # f = open(filename, 'w')
        # rawDataRecord = []

        # recorderData = CANoe.SendDiagRequestPlatform_zFAS_Recorder_APH()

        # if recorderData != None:
            # for x in recorderData:
                # f.write(': ' + str(x) + ';' + str(x) + '\n')  # python will convert \n to os.linesep
        # f.close()
        # os.rename(filename, filename[:-4] + '.par')
        # print "zFAS Recorder file is ready."

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SSH_eMMC_Health_Status(self):
        """Get raw response of SSH DD3 RAM faults.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SSH DD3 RAM faults if positive response is received

        :rtype: string[]
        :returns: Raw response of SSH DD3 RAM faults,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SSH_eMMC_Health_Status")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):

            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            # print "Response raw: "
            # print responseRaw
            return responseRaw  # [''.join(responseRaw[0:4]), ''.join(responseRaw[4:8])]

        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SSH_eMMC_Register(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SSH_eMMC_Register")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):
            response = resp.GetParameter("Param_EXTCSD")
            return response
        else:
            return None

    # returns processed RAW data
    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SSH_Memory_Health(self, param=''):
        """



        :param param:  (Default value = '')



        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SSH_Memory_Health")

        resp = self.SendRequestWaitResponse(diagReq)
        # RAW response format:
        # 4 bytes for each: errors L2, errors OCRAM, errors SDRAM,
        # address of ECC error, number of single bit errors
        # and 8 bytes for observation time
        if self.CheckResponse(resp):
            """
            print resp.GetParameter("Param_AddreOfTheRecenECCErrorInSDRAMContrTextu")
            print resp.GetParameter("Param_NumbeOfSinglBitErrorOnDMATextu")
            print resp.GetParameter("Param_ObersTime")
            print resp.GetParameter("Param_SinglBitErrorL2Textu")
            print resp.GetParameter("Param_SinglBitErrorOCRAMTextu")
            print resp.GetParameter("Param_SinglBitErrorSDRAMTextu")

            print resp.GetParameter("Param_TestProgrAddreOfTheRecenECCErrorInSDRAMContr")
            print resp.GetParameter("Param_TestProgrNumbeOfSinglBitErrorOnDMA")
            print resp.GetParameter("Param_TestProgrSinglBitErrorL2")
            print resp.GetParameter("Param_TestProgrSinglBitErrorOCRAM")
            print resp.GetParameter("Param_TestProgrSinglBitErrorSDRAM")
            """

            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            # print "Response raw:"
            # print responseRaw

            val_observed = [''.join(responseRaw[i:i + 4]) for i in range(0, 20, 4)]
            val_observed.append(''.join(responseRaw[-8:]))
            if param == '':   # return all.
                # note!
                # order of elements is the same as in DeMesswerte_BISTQMSSH DePlatform_zFAS_SSH_Memory_Health_0x1032
                resp = [''.join(responseRaw[12:16]),
                        ''.join(responseRaw[16:20]),
                        ''.join(responseRaw[20:]),
                        ''.join(responseRaw[0:4]),
                        ''.join(responseRaw[4:8]),
                        ''.join(responseRaw[8:12])]
                return resp
            elif param == "Single_bit_errors_L2":
                return ''.join(responseRaw[0:4])
            elif param == "Single_bit_errors_SDRAM":
                return ''.join(responseRaw[8:12])
            elif param == "Address_of_the_recent_ECC_error_in_SDRAM_controller":
                return ''.join(responseRaw[12:16])
            elif param == "Oberservation_Time":
                tmp = responseRaw[20:]
                tmp.reverse()
                return ''.join(tmp)

        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_APH_Memory_Health(self, param=''):
        """



        :param param:  (Default value = '')



        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_APH_Memory_Health")

        resp = self.SendRequestWaitResponse(diagReq)
        # RAW response format:
        # 4 bytes for each: errors L2, errors OCRAM, errors SDRAM,
        # address of ECC error, number of single bit errors
        # and 8 bytes for observation time
        if self.CheckResponse(resp):

            SRAM_errors = resp.GetParameter("Param_TestProgrSRAMCorreECCError")
            Addr_SRAM = resp.GetParameter("Param_TestProgrAddreOfLastErrorSRAM")
            DFlash_errors = resp.GetParameter("Param_DFlasCorreECCError")
            Addr_DCACHE = resp.GetParameter("Param_TestProgrAddreOfLastErrorDCACHDSPR")
            Data_errors = resp.GetParameter("Param_TestProgrDataCorreECCError")
            Oberserv_Time = resp.GetParameter("Param_ObersTime")
            Addr_PCACHE = resp.GetParameter("Param_TestProgrAdresOfLastErrorPCACHPSPR")
            Addr_PFLASH = resp.GetParameter("Param_AddreOfLastErrorPFLAS")
            Program_errors = resp.GetParameter("Param_TestProgrProgrCorreECCError")
            PFlash_errors = resp.GetParameter("Param_PFlasCorreECCError")

            return [SRAM_errors, Addr_SRAM, DFlash_errors, Addr_DCACHE,
                    Data_errors, Oberserv_Time, Addr_PCACHE,
                    Addr_PFLASH, Program_errors, PFlash_errors]
        else:
            return None

    @func_wrapper
    def SendDiagRequestState_DSDL_Hosts(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")
        diagReq.SetParameter("Param_RecorDataIdent", "State_DSDL_Hosts")

        resp = self.SendRequestWaitResponse(diagReq)

        if (self.CheckResponse(resp)):
            self.log.info("%s positive response received!\n"
                          % diagReq.Responses.Count)

            APH = resp.GetParameter("Param_APH")
            SSH = resp.GetParameter("Param_SSH")
            SRH = resp.GetParameter("Param_SRH")
            MVH = resp.GetParameter("Param_MVH")

            return [APH, SSH, SRH, MVH]
        else:
            return None

    @func_wrapper
    def SendDiagRequestDataSetIdentification(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentECUIdent")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "VW_Application_data_set_identification")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp):
            self.log.info("%s positive response received!\n"
                          % diagReq.Responses.Count)

            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            responseDict = {}
            subDict = {'app': None,
                       'plausable': None,
                       'valid': None
                       }

            limit = (len(responseRaw)/7)
            for i in range(0, limit):
                binary = ''
                lastByte = responseRaw[6+i*7]
                binary = format(int(lastByte, 16), '#06b')[2:]

                myDict = dict(subDict)
                myDict['app'] = True if binary[1] == "1" else False
                myDict['plausable'] = True if binary[2] == "1" else False
                myDict['valid'] = True if binary[3] == "1" else False
                responseDict[responseRaw[0+i*7] + responseRaw[1+i*7]] = myDict

            return responseDict

    @func_wrapper
    def SendDiagRequestInternalPowerSupplies(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")
        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_Internal_Power_Supplies")

        resp = self.SendRequestWaitResponse(diagReq)

        if (self.CheckResponse(resp)):
            self.log.debug("%s positive response received!\n"
                          % diagReq.Responses.Count)
            VBATMAIN = resp.GetParameter("Param_VBATMAIN")
            QualiVBATMAIN = resp.GetParameter("Param_QualiVBATMAIN")
            KL30LOCALVM = resp.GetParameter("Param_KL30LOCALVM")
            QualiKL30LOCALVM = resp.GetParameter("Param_QualiKL30LOCALVM")
            KL30MAINVM = resp.GetParameter("Param_KL30MAINVM")
            QualiKL30MAINVM = resp.GetParameter("Param_QualiKL30MAINVM")
            LINFRNT = resp.GetParameter("Param_SUPLINFRNT")
            LINREAR = resp.GetParameter("Param_SUPLINREAR")

            return [VBATMAIN,
                    KL30LOCALVM,
                    KL30MAINVM,
                    QualiVBATMAIN,
                    QualiKL30LOCALVM,
                    QualiKL30MAINVM,
                    LINFRNT,
                    LINREAR]
        else:
            return None

    @func_wrapper
    def SendDiagRequestDiagnosticSession(self, session):
        """



        :param session:



        """

        diagDev = self.InitDiagnostic()
        if diagDev is None:
            return None
        if session == "extended":
            diagReq = diagDev.CreateRequest("DiagnServi_DiagnSessiContrExtenSessi")
        elif session == "programming":
            diagReq = diagDev.CreateRequest("DiagnServi_DiagnSessiContrECUProgrSessi")
        elif session == "development":
            diagReq = diagDev.CreateRequest("DiagnServi_DiagnSessiContrDevelSessi")
        elif session == "default":
            diagReq = diagDev.CreateRequest("DiagnServi_DiagnSessiContrOBDIIAndVWDefauSessi")
        elif session == "eol":
            diagReq = diagDev.CreateRequest("DiagnServi_DiagnSessiContrVWEndOfLineSessi")

        self.log.debug("Sending request for %s diagnostic session!\n" % session)

        resp = self.SendRequestWaitResponse(diagReq)

        if (self.CheckResponse(resp)):
            self.log.debug("Checking active session...\n")
            res = self.SendDiagRequestActiveSession()
            if res is None:
                self.log.error("Couldn't get the response for active "
                               "session!")
                return None
            else:
                self.log.debug("Active session: %s" % res)
                return res

        else:
            return None

    @func_wrapper
    def SendDiagRequestActiveSession(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentECUIdent")
        diagReq.SetParameter("Param_RecorDataIdent", "Active Diagnostic Session")

        resp = self.SendRequestWaitResponse(diagReq)

        if (self.CheckResponse(resp)):
            return resp.GetParameter("Param_ActivDiagnSessi")
        else:
            return None

    @func_wrapper
    def ClearDiagnosticInformation(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ClearDiagnInfor")
        diagReq.Send()

        while diagReq.Pending:
            time.sleep(0.5)

        count = 0
        while ((diagReq.Responses.Count == 0) and (count < 10)):
            self.log.warning("No Response received!")
            self.log.debug("Sending request again!")
            diagReq.Send()
            time.sleep(1)
            count += 1

        if diagReq.Responses.Count == 0:
            self.log.warning("No Response received for more than 10 tries!")
            return None
        else:
            resp = diagReq.Responses(1)
            return self.CheckResponse(resp)

    @func_wrapper
    def SendDiagRequestExpectDTC(self, dtcInput):
        """



        :param dtcInput:



        """

        self.log.debug("Searching for DTC: %s" % dtcInput)
        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDTCInforReporDTCByConfiAndPendiStatu")
        diagReq.Send()

        intInput = int(dtcInput, 16)
        hexInput = hex(intInput)

        while diagReq.Pending:
            time.sleep(0.5)

        count = 0
        while ((diagReq.Responses.Count == 0) and (count < 10)):
            self.log.warning("No Response received!")
            self.log.debug("Sending request again!")
            diagReq.Send()
            time.sleep(1)
            count += 1

        if diagReq.Responses.Count == 0:
            self.log.warning("No Response received for more than 10 tries!")
            return None
        else:
            resp = diagReq.Responses(1)
            if resp.Positive:
                self.log.debug("%s positive response received!\n"
                              % diagReq.Responses.Count)

                iterCount = resp.GetComplexIterationCount("Param_DTCAndStatuRecor")
                for i in range(iterCount):
                    dtcDec = resp.GetComplexParameter("Param_DTCAndStatuRecor", i, "Param_DTCUDS", 1)

                    dtcHex = hex(dtcDec)

                    if hexInput == dtcHex:
                        self.log.debug("DTC found: %s" % str(dtcHex))
                        return True

                dtcInfo = self.SendDiagRequestGetDTCInfo(dtcInput)
                if dtcInfo is None:
                    self.log.debug("DTC not found!!!")
                    return False
                else:
                    if "Not" in dtcInfo[1]:
                        self.log.debug("DTC not found (not confirmed)!!!")
                        return False
                    else:
                        self.log.debug("DTC found: %s (%s)"
                                      % (str(dtcHex), str(dtcInfo[0])))
                        return True

    @func_wrapper
    def SendDiagRequestAllConfirmedDTC(self):
        returnList = []
        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDTCInforReporDTCByConfiAndPendiStatu")
        diagReq.Send()

        while diagReq.Pending:
            time.sleep(0.5)

        count = 0
        while ((diagReq.Responses.Count == 0) and (count < 10)):
            self.log.warning("No Response received!")
            self.log.debug("Sending request again!")
            diagReq.Send()
            time.sleep(1)
            count += 1

        if diagReq.Responses.Count == 0:
            self.log.warning("No Response received for more than 10 tries!")
            return returnList
        else:
            resp = diagReq.Responses(1)
            if resp.Positive:
                self.log.debug("%s positive response received!\n"
                              % diagReq.Responses.Count)

                iterCount = resp.GetComplexIterationCount("Param_DTCAndStatuRecor")
                for i in range(iterCount):
                    dtcDec = resp.GetComplexParameter("Param_DTCAndStatuRecor",
                                                      i,
                                                      "Param_DTCUDS",
                                                      1)

                    dtcHex = hex(dtcDec)
                    returnList.append(dtcHex)

            return returnList

    @func_wrapper
    def SendDiagRequestExpectActiveDTC(self, dtcInput):
        """



        :param dtcInput:



        """

        self.log.debug("Searching for DTC: %s" % dtcInput)
        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDTCInforReporDTCByActivStatu")
        diagReq.Send()

        intInput = int(dtcInput, 16)
        hexInput = hex(intInput)

        while diagReq.Pending:
            time.sleep(0.5)

        count = 0
        while ((diagReq.Responses.Count == 0) and (count < 10)):
            self.log.warning("No Response received!")
            self.log.debug("Sending request again!")
            diagReq.Send()
            time.sleep(1)
            count += 1

        if diagReq.Responses.Count == 0:
            self.log.warning("No Response received for more than 10 tries!")
            return None
        else:
            resp = diagReq.Responses(1)
            if resp.Positive:
                self.log.debug("%s positive response received!\n"
                              % diagReq.Responses.Count)

                iterCount = resp.GetComplexIterationCount("Param_DTCAndStatuRecor")
                for i in range(iterCount):
                    dtcDec = resp.GetComplexParameter("Param_DTCAndStatuRecor", i, "Param_DTCUDS", 1)

                    dtcHex = hex(dtcDec)

                    if hexInput == dtcHex:
                        self.log.debug("DTC found: %s" % str(dtcHex))
                        return True

                self.log.debug("DTC not found!!!")
                return False

    @func_wrapper
    def SendDiagRequestGetDTCInfo(self, dtcInput):
        """



        :param dtcInput:



        """

        self.log.debug("Searching info for DTC: %s" % dtcInput)
        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDTCInforReporDTCExtenDataRecorByDTCNumbe")

        intInput = int(dtcInput, 16)
        hexInput = hex(intInput)

        diagReq.SetParameter("Param_DTCMaskRecorGroupOfDTC", hexInput)
        diagReq.SetParameter("Param_DTCExtenDataRecorNumbe", "Standard DTC Information")

        diagReq.Send()

        while diagReq.Pending:
            time.sleep(0.5)

        count = 0
        while ((diagReq.Responses.Count == 0) and (count < 10)):
            self.log.warning("No Response received!")
            self.log.debug("Sending request again!")
            diagReq.Send()
            time.sleep(1)
            count += 1

        if diagReq.Responses.Count == 0:
            self.log.warning("No Response received for more than 10 tries!")
            return None
        else:
            resp = diagReq.Responses(1)
            if resp.Positive:
                self.log.debug("%s positive response received!\n"
                              % diagReq.Responses.Count)

                hexInput = hexInput[:2] + hexInput[2:].upper()
                if hexInput == resp.GetParameter("Param_DTCValue"):
                    status = resp.GetParameter("Param_StatuOfDTCBit0")
                    confirmed = resp.GetParameter("Param_StatuOfDTCBit3")
                    return (status, confirmed)
                else:
                    self.log.warning("Received response is not for specified DTC!")

        return None

    @func_wrapper
    def SendDiagRequestClearFaultMemory(self):
        """ """

        diagDev = self.InitDiagnostic(log=False)
        diagReq = diagDev.CreateRequest("DiagnServi_ClearDiagnInfor")
        resp = self.SendRequestWaitResponse(diagReq)

        return self.CheckResponse(resp)

    @func_wrapper
    def SendDiagRequestHWvariant(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentECUIdent")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "VW ECU Hardware Number")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp):
            HWNumber = resp.GetParameter("Param_VWECUHardwNumbe")
            HWVariant = HWNumber.strip()[-1:]
            if HWVariant == "0":
                self.log.debug("\nTesting HW Variant: A0\n")
                return "A0"
            else:
                self.log.debug("\nTesting HW Variant: %s\n" % HWVariant)
                return HWVariant
        else:
            return None

    @func_wrapper
    def SendDiagRequestSWversion(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentECUIdent")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "VW Application Software Version Number")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp):
            SWversion = resp.GetParameter("Param_VWAppliSoftwVersiNumbe")
            self.log.debug("\nTesting SW Version: %s\n" % SWversion)
            return SWversion
        else:
            return None
        
    @func_wrapper
    def SendDiagRequestBlockVersions(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentECUIdent")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "VW Logical Software Block Version")

        resp = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(resp):
            blockVersions = {}
            gen = (block for block in flashparams['PIE'].keys() if block != 'FF')
            for block in gen:
                blockVer = resp.GetParameter("Param_DataBlock%s" % block)
                if blockVer == '----':
                    blockVer = None
                blockVersions[block] = blockVer
            return blockVersions
        else:
            return None
        
    @func_wrapper
    def SendDiagRequestKeyOffOnReset(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ECUResetKeyOffOnReset")
        resp = self.SendRequestWaitResponse(diagReq)

        return self.CheckResponse(resp)

    @func_wrapper
    def SendDiagRequestEOL(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_DiagnSessiContrVWEndOfLineSessi")
        resp = self.SendRequestWaitResponse(diagReq)

        return self.CheckResponse(resp)

    @func_wrapper
    def SendDiagRequestPlatformZfasHilMode(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentCalibData")
        diagReq.SetParameter("Param_RecorDataIdent", "Platform_zFAS_hil_mode")

        resp = self.SendRequestWaitResponse(diagReq)

        return self.CheckResponse(resp)

    @func_wrapper
    def SendDiagRequestHardReset(self):
        """ """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ECUResetHardReset")
        resp = self.SendRequestWaitResponse(diagReq)

        return self.CheckResponse(resp)

    @func_wrapper
    def SendDiagRequestGlobalTime(self):
        """Read ZGT
        -Initialize diagnostics,
        -create request and set parameters,
        -get ZGT
        :rtype: string[]
        :returns: circular buffer  with ZGT,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_Global_Time")

        resp = self.SendRequestWaitResponse(diagReq)
        self.log.debug("Reading of raw data was successful!")
        responseRaw = []
        if self.CheckResponse(resp):
            ErrorHandlerArr = resp.Stream
            for c in ErrorHandlerArr:
                responseRaw.append(hex(ord(c)))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return responseRaw
        else:
            return None

    @func_wrapper
    def SendDiagRequestPlatform_zFAS_SRH_Source_of_Last_Reset(self):
        """Get raw response of SRH source of last reset.

        -Initialize diagnostics,
        -create request and set parameters,
        -get raw response of SRH source of last reset if positive response is
        received

        :rtype: string[]
        :returns: Raw response of SRH source of last reset,
        None if response is negative
        """

        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDataByIdentMeasuValue")

        diagReq.SetParameter("Param_RecorDataIdent",
                             "Platform_zFAS_SRH_Source_of_Last_Reset")

        resp = self.SendRequestWaitResponse(diagReq)

        if self.CheckResponse(resp):

            responseRaw = []
            stream = resp.Stream
            for c in stream:
                responseRaw.append(format(ord(c), '02x'))

            del responseRaw[2]
            del responseRaw[1]
            del responseRaw[0]

            return [''.join(responseRaw)]

        else:
            return None

    @func_wrapper
    def SendDiagRequestProductionMode(self, mode=None):
        """Activate or deactivate production mode.

        -Initialize diagnostics,
        -create request and set parameters,
        -check if request is fullfiled

        :type mode: str
        :param mode: activate or deactivate producton mode
                (Default value = None)

        :rtype: bool
        :returns: True if request is fullfiled, False if not
        """
        if mode is not None:
            diagDev = self.InitDiagnostic()

            diagReq = diagDev.CreateRequest("DiagnServi_WriteDataByIdentCalibData")
            if mode == 'deactivate':
                diagReq.SetParameter("Param_RecorDataIdent",
                                     0x04FC)
                diagReq.SetParameter("Param_ProduDeact",
                                     000000)
                self.log.debug("Dectivating production mode...")
            elif mode == 'activate':
                diagReq.SetParameter("Param_RecorDataIdent",
                                     0x04FE)
                diagReq.SetParameter("Param_InhibAutomParki",
                                     01)
                self.log.debug("Activating production mode...")
            else:
                self.log.error("Diag service mode is not correct")
                return False

            resp = self.SendRequestWaitResponse(diagReq)

            return self.CheckResponse(resp)
        else:
            return False

    @func_wrapper
    def SendDiagRequestRepairShopMode(self):
        """Activate or deactivate repair shop mode.

        -Initialize diagnostics,
        -create request and set parameters,
        -check if request is fullfiled

        :rtype: bool
        :returns: True if request is fullfiled, False if not
        """

        diagDev = self.InitDiagnostic()

        diagReq = diagDev.CreateRequest("DiagnServi_WriteDataByIdentECUIdent")

        diagReq.SetParameter("Param_RecorDataIdent",
                             0xF198)

        self.log.debug("Sending Repair Shop Code Or Tester Serial Number...")
        resp = self.SendRequestWaitResponse(diagReq)

        return self.CheckResponse(resp)

    @func_wrapper
    def GetECUResponseTimeout(self):
        ecu = self.GetActiveECU()
        if ecu is False:
            return False
        else:
            return int(ecu.ResponseTimeout)

    @func_wrapper
    def ResetAdaptions(self):
        diagDev = self.InitDiagnostic()

        if self.SendDiagRequestGetSecurityAccess() is not True:
            return None

        diagReq = diagDev.CreateRequest("DiagnServi_RoutiContrStartBasicSetti")
        diagReq.SetParameter("Param_RoutiIdent", "Reset of all adaptions")
        diagReq.SetParameter("Param_RoutiContrOptio", "Basic_Settings")

        response = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(response):
            return True
        else:
            return False
            
    @func_wrapper
    def GetDTCCount(self):
        diagDev = self.InitDiagnostic()
        diagReq = diagDev.CreateRequest("DiagnServi_ReadDTCInforReporDTCByConfiAndPendiStatu")
        response = self.SendRequestWaitResponse(diagReq)
        if self.CheckResponse(response):
            iterCount = response.GetComplexIterationCount("Param_DTCAndStatuRecor")
            return iterCount
        else:
            return False