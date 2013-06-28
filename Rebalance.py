#!/usr/bin/env python
#
# Author: Ming Liu
# Description: This file implements four basic performance states rebalance methods:
# Optimal, evenly rebalance, priority selection
#

class Instance:
	type = ""
	domID = -1 
	currentState = -1
	targetState = -1
	tmp = -1
	priority = -1
	perfDegrade_list = []
	powerConsume_list = []

	# Constructor
	def __init__(self, type, domID, state, priority, pd_list, pc_list):
	  self.type = type
	  self.domID = domID
	  self.currentState = state
	  self.targetState = -1
	  self.tmp = -1
	  self.priority = priority
	  self.perfDegrade_list = pd_list
	  self.powerConsume_list = pc_list

	# Print Instance Information
	def printIstance(self):
	  print "Type: ", self.type
	  print "DomainID: ", self.domID
	  print "Current State: ", self.currentState
	  print "Target State: ", self.targetState
	  print "Priority: ", self.priority
	  print "PerfDegrade_list: ", self.perfDegrade_list
	  print "PowerConsume_list: ", self.powerConsume_list

	# Destructor
	def __del__(self):
	  pass

class PStateRebalance:
	instance_pool = []
	
	# Constructor
	def __init__(self):
	  self.instance_pool = []
	
	# Destructor
	def __del__(self):
	  pass

	# Get Instance pool
	def getInstancePool(self):
	  return self.instance_pool

	# Add Instance
	def addInstance(self, instance):
	  self.instance_pool.append(instance)

	# Optimal Finding, Recursion
	def __OptimalFind(self, cur, all, power, degradation):
	  i = self.instance_pool[cur].currentState
	  maxPower = power

	  while i >= 0:
	    self.instance_pool[cur].tmp = i
	    if cur != all:
	      maxPower = self.__OptimalFind(cur+1, all, maxPower, degradation)
	    else:
	      accumulate_degradation = 0
	      accumulate_power = 0

	      for j in self.instance_pool:
	        accumulate_degradation += (j.perfDegrade_list[j.tmp] - j.perfDegrade_list[j.currentState])
	        accumulate_power += (j.powerConsume_list[j.currentState] - j.powerConsume_list[j.tmp])

	      if accumulate_degradation <= float(degradation) and accumulate_power >= maxPower:
		maxPower = accumulate_power
	        for k in self.instance_pool:
		  k.targetState = k.tmp
	    i -= 1
	  return maxPower

	# Evenly Finding
	def __EvenlyFind(self, degradation):
          accumulate_degradation = 0
	  accumulate_power = 0
	  maxPower = 0
          flag = 0

	  for i in self.instance_pool:
	    i.targetState = i.currentState

	  while flag == 0:
            accumulate_degradation = 0
	    accumulate_power = 0

	    for i in self.instance_pool:
	      if accumulate_degradation <= float(degradation):
	        if i.targetState > 0:
	          i.targetState = i.targetState - 1
	          accumulate_degradation += (i.perfDegrade_list[i.targetState] - i.perfDegrade_list[i.currentState])
	          accumulate_power += (i.powerConsume_list[i.currentState] - i.powerConsume_list[i.targetState])
	        else:
	          accumulate_degradation += (i.perfDegrade_list[i.targetState] - i.perfDegrade_list[i.currentState])
	          accumulate_power += (i.powerConsume_list[i.currentState] - i.powerConsume_list[i.targetState])
	      else:
		flag = 1
	 	break
	    
	    if accumulate_degradation > float(degradation):
	      flag = 1

	    test = 0
	    for j in self.instance_pool:
	      if j.targetState != 0:
	        test = 1
	 	break

	    if test == 0:
	      flag = 1

	  return accumulate_power
	  
	# Priority Finding
	def __PriorityFind(self, degradation):
	  priority = 0
	  accumulate_degradation = 0
	  accumulate_power = 0

	  for i in self.instance_pool:
	    i.targetState = i.currentState

	  while priority <= 1:
	    for i in self.instance_pool:
	      if i.priority == priority:
	        j = i.currentState
		while j > 0:
		  accumulate_degradation = 0
		  for k in self.instance_pool:
		    accumulate_degradation += (k.perfDegrade_list[k.targetState] - k.perfDegrade_list[k.currentState])

		  if accumulate_degradation <= float(degradation):
		    j -= 1
		  else:
		    break
		  i.targetState = j

	    priority += 1

	  accumulate_degradation = 0
	  accumulate_power = 0
	  for i in self.instance_pool:
	    accumulate_degradation += (i.perfDegrade_list[i.targetState] - i.perfDegrade_list[i.currentState])
	    accumulate_power += (i.powerConsume_list[i.currentState] - i.powerConsume_list[i.targetState])

	  return accumulate_power

	# Rebalance performance states
	def rebalance(self, increasedPower, Method, Degradation):
	  if int(Method) == 0: #Optimal
	    targetPower = self.__OptimalFind(0, len(self.instance_pool) - 1, 0, Degradation)
	    print "Optimal: ", targetPower
	  elif int(Method) == 1: # Evenly Balance
	    targetPower = self.__EvenlyFind(Degradation)
	    print "Evenly Balance: ", targetPower 
	  elif int(Method) == 2: # Priority Selection
	    targetPower = self.__PriorityFind(Degradation)
	    print "Priority Selection: ", targetPower
	  else:
	    targetPower = 0.0
	    for i in self.instance_pool:
	      i.targetState = i.currentState
	    print "Unknown Method", targetPower


	# Print instance pool
	def printInstancePool(self):
	  for i in self.instance_pool:
	    print i.printIstance()
