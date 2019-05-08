# -----------------------------------------------------------------------------
# # Copyright (C) 2013 TTTech Computertechnik AG. All rights reserved
# Schoenbrunnerstrasse 7, A--1040 Wien, Austria. office@tttech.com
#
# ++
# Name
#    CANoeAPI_MoWi
#
# Purpose
#    API for Vector CANoe (MoWi).
#
#
# Revision Dates
#      05-Apr-2018 eVTE: Creation. Implementation of CANoeAPI_MoWi class.
#
# Status: Development
# -----------------------------------------------------------------------------


from Utils.CANoeAPI import CANoeAPI_base


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
                    time.time() < start_ts + 60):
                pass
            return_value = self.request['response_data']
            self.request['response_ready'] = False
            self.request['args'] = tuple()
            self.request['kwargs'] = dict()
        return return_value
    return wrapper
    

class CANoeAPI(CANoeAPI_base):
    """CANoeAPI_MoWi class."""
    def __init__(self, input_obj):
        """Creates variables associated with the class."""
        self.te_obj = input_obj
        super(CANoeAPI, self).__init__()
        
        #=======================================================================
        # self.FlexRayNetwork = "MLBevo_Fx_Cluster"
        # self.DiagNetwork = self.FlexRayNetwork
        # self.DiagDeviceName = "BV_FrontSensoDriveAssisSysteUDS"
        # self.SystemState = "CtCdLCSM.PpPFProvidedData.DeLCSSystemState"
        # self.SystemStateVar = self.SystemState.replace(".", "_")
        # self.XCPns = XCPns
        # self.PowerModuleNS = "VTS::M_PWR_ECU_KL30_PWR"
        #=======================================================================

