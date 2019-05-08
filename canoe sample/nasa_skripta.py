# -----------------------------------------------------------------------------
# Example: Test Feature Set via Python
#
# This sample demonstrates how to start the test modules and test
# configurations via COM API using a Python script.
# The script uses the included PythonBasicEmpty.cfg configuration but is
# working also with any other CANoe configuration containing test modules
# and test configurations.
#
# Limitations:
#  - only the first test environment is supported. If the configuration
#    contains more than one test environment, the other test environments
#    are ignored
#  - the script does not wait for test reports to be finished. If the test
#    reports are enabled, they may run in the background after the test is
#    finished
# -----------------------------------------------------------------------------
# Copyright (c) 2017 by Vector Informatik GmbH.  All rights reserved.
# -----------------------------------------------------------------------------

import time
import os
import msvcrt
from win32com.client import *
from win32com.client.connect import *


def DoEvents():
    pythoncom.PumpWaitingMessages()
    time.sleep(.1)


def DoEventsUntil(cond):
    while not cond():
        DoEvents()


class CanoeSync(object):
    """Wrapper class for CANoe Application object"""
    Started = False
    Stopped = False
    ConfigPath = ""

    def __init__(self):
        app = DispatchEx('CANoe.Application')
        app.Configuration.Modified = False
        ver = app.Version

        print "loaded canoe version" + \
            str(ver.major) + str(ver.minor) + str(ver.Build)
        self.App = app
        self.TestConfigs = app.Configuration.TestConfigurations
        self.Measurement = app.Measurement
        self.Running = lambda: self.Measurement.Running
        self.WaitForStart = lambda: DoEventsUntil(lambda: CanoeSync.Started)
        self.WaitForStop = lambda: DoEventsUntil(lambda: CanoeSync.Stopped)
        WithEvents(self.App.Measurement, CanoeMeasurementEvents)

    def Load(self, cfgPath):
        # current dir must point to the script file
        cfg = os.path.join(os.curdir, cfgPath)
        cfg = os.path.abspath(cfg)
        print('Opening: ', cfg)
        self.ConfigPath = os.path.dirname(cfg)
        self.Configuration = self.App.Configuration
        self.App.Open(cfg)

    def LoadTestSetup(self, testsetup):
        self.TestSetup = self.App.Configuration.TestSetup
        path = os.path.join(self.ConfigPath, testsetup)
        for i in range(self.TestSetup.TestEnvironments.Count):
            self.TestSetup.TestEnvironments.Remove(i + 1, False)

        testenv = self.TestSetup.TestEnvironments.Add(path)
        self.TestSetup.TestEnvironments.Item(1).Enabled = True
        self.TestSetup.TestEnvironments.Item(1).ExecuteAll
        print "Broj environmenta: " + \
            str(self.TestSetup.TestEnvironments.Count)
        print "Ime environmenta: " + \
            str(self.TestSetup.TestEnvironments.Item(1).Name)
        print "Putanja environmenta: " + \
            str(self.TestSetup.TestEnvironments.Item(1).FullName)

        testenv = CastTo(testenv, "ITestEnvironment2")
        self.TestEnv = testenv
        # TestModules property to access the test modules
        self.TestModules = []
        self.TraverseTestItem(
            testenv, lambda tm: self.TestModules.append(CanoeTestModule(tm)))
        print "Broj testnih modula unutar enviromenta je : " + \
            str(len(self.TestModules))
        for i in range(len(self.TestModules)):
            print "Ime testnog modula %s :" % (
                i) + str(self.TestModules[i].Name)

    def AddTestModules(self, nameOfTestModule):
        pathModule = os.path.join(self.ConfigPath, nameOfTestModule)
        self.TestEnv.TestModules.Add(pathModule)

    def LoadTestConfiguration(self, testcfgname, testunits):
        """ Adds a test configuration and
         initialize it with a list of existing test units """
        tc = self.App.Configuration.TestConfigurations.Add()
        print "Broj testnih konfiguracija: " + \
            str(self.App.Configuration.TestConfigurations.Count)
        for i in range(self.App.Configuration.TestConfigurations.Count):
            print self.App.Configuration.TestConfigurations.Item(i+1).Name
        tus = CastTo(tc.TestUnits, "ITestUnits2")
        for tu in testunits:
            tus.Add(tu)
        # TestConfigs property to access the test configuration
        self.TestConfigs = [CanoeTestConfiguration(tc)]

    def Start(self):
        if not self.Running():
            self.Measurement.Start()
            self.WaitForStart()

    def Stop(self):
        if self.Running():
            self.Measurement.Stop()
            self.WaitForStop()

    def RunTestModules(self):
        """ starts all test modules and waits for all of them to finish"""
        # start all test modules
        for tm in self.TestModules:
            tm.Start()

        # wait for test modules to stop
        while not all([not tm.Enabled or tm.IsDone()
                       for tm in app.TestModules]):
            DoEvents()

    def RunTestConfigs(self):
        """ starts all test configurations
         and waits for all of them to finish"""
        # start all test configurations
        for tc in self.TestConfigs:
            tc.Start()

        # wait for test modules to stop
        while not all([not tc.Enabled or tc.IsDone()
                       for tc in app.TestConfigs]):
            DoEvents()

    def TraverseTestItem(self, parent, testf):
        for test in parent.TestModules:
            testf(test)
        for folder in parent.Folders:
            found = self.TraverseTestItem(folder, testf)


class CanoeMeasurementEvents(object):
    """Handler for CANoe measurement events"""

    def OnStart(self):
        CanoeSync.Started = True
        CanoeSync.Stopped = False
        print("< measurement started >")

    def OnStop(self):
        CanoeSync.Started = False
        CanoeSync.Stopped = True
        print("< measurement stopped >")


class CanoeTestModule:
    """Wrapper class for CANoe TestModule object"""

    def __init__(self, tm):
        self.tm = tm
        self.Events = DispatchWithEvents(tm, CanoeTestEvents)
        self.Name = tm.Name
        self.IsDone = lambda: self.Events.stopped
        self.Enabled = tm.Enabled

    def Start(self):
        if self.tm.Enabled:
            self.tm.Start()
            self.Events.WaitForStart()


class CanoeTestConfiguration:
    """Wrapper class for a CANoe Test Configuration object"""

    def __init__(self, tc):
        self.tc = tc
        self.Name = tc.Name
        self.Events = DispatchWithEvents(tc, CanoeTestEvents)
        self.IsDone = lambda: self.Events.stopped
        self.Enabled = tc.Enabled

    def Start(self):
        if self.tc.Enabled:
            self.tc.Start()
            self.Events.WaitForStart()


class CanoeTestEvents:
    """Utility class to handle the test events"""

    def __init__(self):
        self.started = False
        self.stopped = False
        self.WaitForStart = lambda: DoEventsUntil(lambda: self.started)
        self.WaitForStop = lambda: DoEventsUntil(lambda: self.stopped)

    def OnStart(self):
        self.started = True
        self.stopped = False
        print("<", self.Name, " started >")

    def OnStop(self, reason):
        self.started = False
        self.stopped = True
        print("<", self.Name, " stopped >")


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
app = CanoeSync()

# loads the sample configuration
app.Load(r'CANoeConfig\PythonBasicEmpty.cfg')

# add test modules to the configuration
app.LoadTestSetup(r'TestEnvironments\Test Environment.tse')

# add a test configuration and a list of test units
app.LoadTestConfiguration('TestConfiguration', [
                          'TestConfiguration\EasyTest\EasyTest.vtuexe'])

print "Unesi od indeksa kog testa hoces izvrsavanje: "
pocetakTestova = raw_input()
print "Unesi do indeksa kog testa hoces izvrsavanje: "
krajTestova = raw_input()
for i in range(int(krajTestova)):
    testniModul = r'TestModules\test%s.can' % (str(i+1+int(pocetakTestova)))
    print testniModul
    app.AddTestModules(testniModul)


# start the measurement
app.Start()

# runs the test modules
app.RunTestModules()

# runs the test configurations
app.RunTestConfigs()

# wait for a keypress to end the program
print("Press any key to exit ...")
while not msvcrt.kbhit():
    DoEvents()

# stops the measurement
app.Stop()
