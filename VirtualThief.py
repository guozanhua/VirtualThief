#!/usr/bin/env python
#
# Author: Ming Liu
# Description: This is a scheduler executed in Domain0. It rebalances all VM's
# performance states and steals power from other VM to GPU VM to cap the maximum
# power consumption. Our MICRO paper uses it.
# 
# Usage: python VirtualThief.py [GPU Application Name] [Input Size] [Method] [Degradation]
#
import sys
import os
from Rebalance import PStateRebalance, Instance

# GPU Application increased power database, APC_GPU_DB
class GPUAppPower:
	name = ""
	increasedPower = []

	# Constructor
	def __init__(self, appName=""):
	  self.name = appName
	  self.increasedPower = []

	# Set App Name
	def setName(self, appName):
	  self.name = appName

	# Get App Name
	def getName(self):
	  return self.name

	# Append power data to increased Power
	def addPower(self, powerdata=0):
	  self.increasedPower.append(powerdata)

	# Get increased power array
	def getIncreasedPower(self):
	  return self.increasedPower

	# Print saved Data
	def printData(self):
	  print self.name,
	  for i in self.increasedPower:
	    print i,
	  print

	# Destructor
	def __del__(self):
	  pass

# VCPU class
class VCPU:
	cpu = -1
	pState = -1

	# Constructor
	def __init__(self, cpu, pState):
	  self.cpu = cpu
	  self.pState = pState

	# Get cpu
	def getCPU(self):
	  return self.cpu

	# Get pState
	def getPstate(self):
	  return self.pState

	# Destructor
	def __del__(self):
	  pass

# Virtual Machine Class
class VM:
	type = ""
	name = ""
	id = -1
	cpu_usage = 0.0
	vbd_op = 0
	net_op = 0
	vcpu_list = []

	# Constructor
	def __init__(self, type, name, id, cpu_usage, net_op, vbd_op):
	  self.type = type 
	  self.name = name
	  self.id = id
	  self.cpu_usage = cpu_usage 
	  self.net_op = net_op
	  self.vbd_op = vbd_op
	  self.vcpu_list = []

	# get State
	def getState(self):
	  return self.vcpu_list[0].pState
	
	# get type
	def getType(self):
	  return self.type

	# get Domain ID
	def getDomainID(self):
	  return self.id

	# Print information
	def printVMInfo(self):
	  print "type: ", self.type
	  print "name: ", self.name
	  print "id: ", self.id
	  print "cpu_usage: ", self.cpu_usage
	  print "vbd_op: ", self.vbd_op
	  print "net_op: ", self.net_op
	  for i in self.vcpu_list:
	    print "vcpu: ", i.getCPU(), i.getPstate()

	# Add VCPU into the pool
	def addVCPU(self, vcpu):
	  self.vcpu_list.append(vcpu)

	# Analyze and Set type
	def determineType(self):
	  if self.cpu_usage >= 90.0:
	    self.type = "CPU_VM"
	  elif self.vbd_op >= 200000:
	    self.type = "IO_VM"
	  elif self.net_op >= 500000:
	    self.type = "NET_VM"
	  else:
	    self.type = "IDLE"
	  if self.vbd_op >= 200000 and self.net_op >= 500000:
	    self.type = "TRANSFER_VM"

	  # For Test
	  if self.id == 5:
	    self.type = "IO_VM"
	  if self.id == 6:
	    self.type = "CPU_VM"


	# Get VM's Name
	def getName(self):
	  return self.name

	# Get VM's Domain ID
	def getID(self):
	  return self.id

	# Set ID
	def setId(self, id):
	  self.id = id

	# Destructor
	def __del__(self):
	  pass

class Standard:
	type = ""
	Perf_Degrade = []
	Power_Consume = []

	# Constructor
	def __init__(self, type):
	  self.type = type
	  self.Perf_Degrade = []
	  self.Power_Consume = []

	# get performance degradation
	def getPerfD(self):
	  return self.Perf_Degrade

	# get power consumption
	def getPowerC(self):
	  return self.Power_Consume

	# get standard type
	def getType(self):
	  return self.type

	# add profile data
	def addData(self, degrade, consume):
	  self.Perf_Degrade.append(degrade)
	  self.Power_Consume.append(consume)

	# print Standard
	def printStandard(self):
	  print self.type
	  print "Performance Degradation"
	  for i in self.Perf_Degrade:
	    print i,
	  print
	  print "Power Consumption"
	  for i in self.Power_Consume:
	    print i,
	  print

	# Destructor
	def __del__(self):
	  pass

# VM Indentifier Class
class Identifier:
	VM_Pool = []
	VM_Standard = []

	# Constructor
	def __init__(self):
	  self.VM_Pool = []
	  self.VM_Standard = []

	# Get VM_Pool
	def getVMPool(self):
	  return self.VM_Pool

	# Get VM_Standard
	def getVMStandard(self):
	  return self.VM_Standard

	# Initialize VM Classification Standards and Basic Profil Data
	# CPU, CPU_MEM, IO, NET, TRANSFER, IDLE
	def initializeST(self):
	  try:
	    fd = open("VM_PowerPerformance.txt", "r")
	    fd.close()
	  except IOError:
	    print "VM_PowerPerformance.txt doesn't existed!"

	  try:
	    fd = open("VM_PowerPerformance.txt", "r")
	    count = 0
	    
	    while 1:
	      line = fd.readline()
	      if not line:
		  break
	      tmpSt = Standard(line.split()[0])
	      while count <= 15:
		line = fd.readline()
		tmpSt.addData(float(line.split()[1]), float(line.split()[2]))
		count += 1
	      count = 0
	      self.VM_Standard.append(tmpSt)

	    fd.close()
	  except IOError:
	    print "VM_PowerPerformance.txt can't be processed!"
	    fd.close()

	# Scan Environment and Characterize VM
	def analyzeVM(self):
	  os.system("xm list > xm_list_tmp.txt")
	  os.system("xentop -b -i 2 -d 1 > xentop_tmp.txt")

	  # Check files exist or not
	  try:
	    fd = open("xentop_tmp.txt", "r")
	    lineno = len(fd.readlines())
	    fd.close()
	  except IOError:
	    print "xentop_tmp.txt doesn't exist!" 

	  try:
	    fd = open("xm_list_tmp.txt")
	    fd.close()
	  except IOError:
	    print "xm_list_tmp.txt doesn't exist!"

	  try:
	    fd = open("VM_VCPU_mapping.txt")
	    fd.close()
	  except IOError:
	    print "VM_VCPU_mapping.txt doesn't exist!"

	  # xentop analysis
	  try:
	    fd = open("xentop_tmp.txt", "r")
	    count = 0

	    while 1:
	      line = fd.readline()
	      if not line:
		  break
	      if count >= (lineno/2 + 1):
		if line.split()[0] == "Domain-0":
		  pass
		else:
		  vm_instance = VM("", line.split()[0], -1, float(line.split()[3]), int(line.split()[10]) + int(line.split()[11]), int(line.split()[14]) + int(line.split()[15]))
		  self.VM_Pool.append(vm_instance)
	      else:
		count += 1
		continue

	    fd.close()
	  except IOError:
	    print "xentop_tmp.txt can't be processed!"
	    fd.close()

	  # xm list analysis
	  try:
	    fd = open("xm_list_tmp.txt", "r")

	    while 1:
	      line = fd.readline()
	      if not line:
		break
	      for i in self.VM_Pool:
		if i.getName() == line.split()[0]:
		  i.setId(int(line.split()[1]))

	    fd.close()
	  except IOError:
	    print "xm_list_tmp.txt can't be processed!"
	    fd.close()

	  # VM vcpu mapping analysis
	  try:
	    fd = open("VM_VCPU_mapping.txt", "r")

	    while 1:
	      line = fd.readline()
	      if not line:
		break
	      if line.split()[0] == "DomainID":
		continue	
	      else:
		for i in self.VM_Pool:
		  if int(line.split()[0]) == i.getID():
		    i.addVCPU(VCPU(int(line.split()[1]),int(line.split()[2])))

	    fd.close()
	  except IOError:
	    print "VM_VCPU_mapping.txt can't be processed!"
	    fd.close()
	
	  for i in self.VM_Pool:
	    i.determineType()

	  os.system("rm xm_list_tmp.txt")
	  os.system("rm xentop_tmp.txt")

	# print VM characterization information
	def printVMPool(self):
	  for i in self.VM_Pool:
	    i.printVMInfo()

	# Print VM Standard information
	def printVMStandard(self):
	  for i in self.VM_Standard:
	    i.printStandard()

	# Destructor
	def __del__(self):
	  pass

# Major Scheduler Class
class VirtualThief:
	APC_GPU_DB = []
	VM_Identifier = Identifier()
	coordinator = PStateRebalance()
	statesPool = [1600000, 1800000, 1900000, 2100000, 2200000, 2400000, 2500000, 2700000, 2900000, 3000000, 3200000, 3300000, 3500000, 3600000, 3800000, 3801000]

	# Constructor
	def __init__(self):
	  self.APC_GPU_DB = []
	  self.VM_Identifier = Identifier()
	  self.coordinator = PStateRebalance()

	# VM_Identifier initialization
	def initialize_VM_Identifier(self):
	  self.VM_Identifier.initializeST()
	  #self.VM_Identifier.printVMStandard()

	# VM characterization
	def characterize_VM(self):
	  self.VM_Identifier.analyzeVM()
	  #self.VM_Identifier.printVMPool()

	# APC_GPU_DB initialization
	def initializeDB(self):
	  try:
	    fd = open("APC_GPU_DB.txt", "r")
	  except IOError:
	    print "APC_GPU_DB.txt doesn't exist!" 

	  try:
	    while 1:
	      line = fd.readline()
	      if not line:
		  break

	      powerEntry = GPUAppPower()
	      j = 0
	      for i in line.split():
		if j == 0:
		  powerEntry.setName(i)
		else:
		  powerEntry.addPower(i)
		j += 1
	      self.APC_GPU_DB.append(powerEntry)

	    fd.close()
	  except IOError:
	    print "APC_GPU_DB.txt can't be processed!"
	    fd.close()

	# get incread power from GPU execution
	def obtainIncreasedPower(self, gpuApp, input):
	  for i in self.APC_GPU_DB:
	    if i.getName() == gpuApp:
	      if int(input) < 0:
	        return None
	      if int(input) >= len(i.getIncreasedPower()):
		return None
	      else:
		return (i.getIncreasedPower())[int(input)]

	# performance state rebalance
	def rebalance(self, gpuIncreasedPower, Method, Degradation):
	  # Set VM instance
	  for i in self.VM_Identifier.getVMPool():
	    state = i.getState()
	    if i.getType() == "CPU_VM" or i.getType() == "CPU_MEM_VM" or i.getType() == "GPU_VM_S":
	      priority = 1
	    else:
	      priority = 0

	    for j in self.VM_Identifier.getVMStandard():
	      if i.getType() == j.getType():
		tmpI = Instance(i.getType(), i.getDomainID(), state, priority, j.getPerfD(), j.getPowerC())
	        self.coordinator.addInstance(tmpI)
		break
	  # State Rebalance Execution
	  self.coordinator.rebalance(gpuIncreasedPower, Method, Degradation) 

	  # Execute xenpm command 
	  for i in self.coordinator.getInstancePool():
	    for j in self.VM_Identifier.getVMPool():
	      if i.domID == j.id:
		for k in j.vcpu_list:
		  cmd = "xenpm set-scaling-speed " + str(k.getCPU()) + " " + str(self.statesPool[i.targetState])
	 	  print cmd
		  os.system(cmd)

	  # print instance pool list
	  #self.coordinator.printInstancePool()

	# Destructor	
	def __del__(self):
	  pass

	# Test function
	def test(self):
	  print "Hello World!"
	  for i in self.APC_GPU_DB:
	    i.printData()

def main(appName, inputSize, Method, Degradation):
	scheduler = VirtualThief()
	scheduler.initializeDB()
	scheduler.initialize_VM_Identifier()

	scheduler.characterize_VM()
	powerGap = scheduler.obtainIncreasedPower(appName, inputSize)

	if powerGap == None:
	  print "No Related value in APC_GPU_DB"
	else:
	  scheduler.rebalance(powerGap, Method, Degradation)

	#scheduler.test()

if __name__ == "__main__":
	if len(sys.argv) != 5:
	  print "Usage: python VirtualThief.py [GPU Application Name] [Input Size] [Method] [Degradation]"
	else:
	  main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
