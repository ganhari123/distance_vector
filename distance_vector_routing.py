import sys


DEBUG = False
output_format = 0

# with open("file.txt") as f:
# 		count = 0
# 		line = f.readline().rstrip('\n')
# 		print(count, " : ", line)
# 		for line in f:
# 			count += 1
# 			l = line.rstrip('\n').split()
# 			l = (int(l[0]), int(l[1]), int(l[2]))
# 			print(count, " : ", l)


def LOG(comment, same_line=False):
	if (DEBUG):
		if same_line:
			print(comment, end="")
		else:
			print(comment)


# with open("file.txt") as f:
# 		count = 0
# 		line = f.readline().rstrip('\n')
# 		print(count, " : ", line)
# 		for line in f:
# 			count += 1
# 			l = line.rstrip('\n').split()
# 			l = (int(l[0]), int(l[1]), int(l[2]))
# 			print(count, " : ", l)


# inital processing of the initial topology file
def process_init_topology(filename):
	with open(filename) as f:
		line = f.readline().rstrip('\n')
		num_routers = int(line)
		init_topology = []
		for line in f:
			numbers = line.rstrip('\n').split()
			numbers = (int(numbers[0]), int(numbers[1]), int(numbers[2]))
			init_topology.append(numbers)
		return num_routers, init_topology


# initial processing of topology events file
def process_topology_events(filename):
	""" returns a dictionary of iteration to list of changes on that iteration """
	with open(filename) as f:
		topology_events = {}
		for line in f:
			numbers = line.rstrip('\n').split()
			iteration = int(numbers[0])
			numbers = [(int(numbers[1]), int(numbers[2]), int(numbers[3]))]
			if iteration in topology_events:
				topology_events[iteration] = topology_events[iteration] + numbers
			else:
				topology_events[iteration] = numbers

		return topology_events


class Node(object):
		""" Class to represent a node in the graph

		Attributes:
			name: a unique number to identify the Node object
			num_routers: number of routers in network (used for simplicity)
			neighbours: a dictionary of node name to node object for neighbors or False if not a neighbor
			distances: a dictionary of neighboring nodes numbers and their distance
			
		"""


		def __init__(self, name, num_routers):
			""" initializes node as detached router """
			self.name = name
			self.num_routers = num_routers
			self.dvTable = {i : {j : float('inf') for j in range(1, num_routers + 1)} for i in range(1, num_routers + 1)}
			self.dvTable[self.name][self.name] = 0
			self.neighbors = []
			self.goal_path = {} # goal : neighbor
			self.next_hop = {} # goal : hop

		def update(self, src_node, dest_node, distance):
			""" updates node distance or adds a new one """
			self.dvTable[src_node.name][dest_node.name] = distance

		def update_neighbors(self, node, remove_flag):
			if remove_flag:
				if node in self.neighbors:
					self.neighbors.remove(node)
			else:
				self.neighbors.append(node)
		def update_dvtable(self, node, table):
			for key, vals in table.items():
				self.dvTable[node][key] = vals

		def remove(self, src_node, dest_node):
			""" removes the given neighbor by router number """
			self.dvTable[src_node][dest_node] = False
			if src_node == self.name and dest_node in self.next_hop:
				del next_hop[dest_node]

		def get_neighbors(self):
			return self.neighbors


class Graph(object):

	""" Graph to represent the network model

	Attibutes:
		topology_init: inital topology of network
		topology_events: topology events for specific iterations
		num_routers: number of routers in network
		nodes: dictionary of each node (router)
		iteration: number of iteration currently running on graph
		protocol: protocol to use, pass in Graph.basic_protocol, Graph.split_horizon or Graph.poison_reverse
		converged: whether or not the algorithm has converged
	"""
			
	def __init__(self, num_routers, topology_init, topology_events):
		""" Initialize the graph for simulation 
			
			Aruguments:
				num_routers: number of routers
				topology_init: list of tuples in form (src_router, dest_router, distance)
				topology_events: dictionary of event time to list of tuples in form (src_router, dest_router, distance)
				protocol: protocol to use
		"""
		self.topology_init = topology_init # Initial topology
		self.topology_events = topology_events # events
		self.num_routers = num_routers # Number of routers
		self.nodes = {i : Node(i, num_routers) for i in range(1, num_routers + 1)} # Declaration of all nodes
		self.iteration = 1 # Round iterations
		# The storage of the next hop and the number of hops
		self.hop_next = {i : {j : (j, 0) for j in range(1, num_routers + 1)} for i in range(1, num_routers + 1)} 
		# Storage of all the direct links
		self.hardLinks = {i : {j : float('inf') for j in range(1, num_routers + 1)} for i in range(1, num_routers + 1)}
		# Setting all the hopes to either -1, -1 or if the same node; node, 0
		for i in range(1, self.num_routers + 1):
			for j in range(1, self.num_routers + 1):
				if i == j:
					self.hop_next[i][j] = (j, 0)
				else:
					self.hop_next[i][j] = (-1, -1)
		# Initialize all links according to the topology
		for link in topology_init:
			from_node, to_node, distance = link
			self.hardLinks[from_node][to_node] = distance
			self.hardLinks[to_node][from_node] = distance
			self.hop_next[from_node][to_node] = (to_node, 1)
			self.hop_next[to_node][from_node] = (from_node, 1)
			self.nodes[from_node].update_neighbors(to_node, False)
			self.nodes[to_node].update_neighbors(from_node, False)
			self.nodes[from_node].update(self.nodes[from_node], self.nodes[to_node], distance)
			self.nodes[to_node].update(self.nodes[to_node], self.nodes[from_node], distance)


	############################
	# Poison Reverse implementation
	def poison_reverse(self):
		if DEBUG: self.debug_display()
		converged = False
		count_to_inf = False
		last_update = 1
		while not converged and self.iteration < 100:
			if output_format == 1:
				print("Round", self.iteration, "\n")
				for i in range(1, self.num_routers + 1):
					print(i, " ", end="")
					for j in range(1, self.num_routers + 1):
						print(self.hop_next[i][j]," ", end="")
					print("\n")
				print("\n")
			converged = True
			if self.iteration in topology_events:
				links = topology_events[self.iteration]
				for link in links:
					from_node, to_node, distance = link
					removeflag = False
					if distance == -1: 
						distance = float('inf')
						removeflag = True
					if to_node in self.nodes[from_node].next_hop:
						del self.nodes[from_node].next_hop[to_node]
					if from_node in self.nodes[to_node].next_hop:
						del self.nodes[to_node].next_hop[from_node]
					self.nodes[from_node].update(self.nodes[from_node], self.nodes[to_node], distance)
					self.hop_next[from_node][to_node] = (to_node, 1)
					self.hardLinks[from_node][to_node] = distance
					self.hardLinks[to_node][from_node] = distance
					self.nodes[to_node].update(self.nodes[to_node], self.nodes[from_node], distance)
					self.hop_next[to_node][from_node] = (from_node, 1)
					self.nodes[from_node].update_neighbors(to_node, removeflag)
					self.nodes[to_node].update_neighbors(from_node, removeflag)
					converged = False
				last_update = self.iteration
				print("Updated Topology:\n")
				del topology_events[self.iteration]
			else:
				self.iteration += 1
				copyDvTable = {z: {i : {j : float('inf') for j in range(1, num_routers + 1)} for i in range(1, num_routers + 1)} for z in range(1, num_routers + 1)}
				for i in range (1, self.num_routers + 1):
					for j in range (1, self.num_routers + 1):
						for k in range(1, self.num_routers + 1):
							copyDvTable[i][j][k] = self.nodes[i].dvTable[j][k]

				for node in range(1, self.num_routers + 1):
					for dest in range(1, self.num_routers + 1):
						if dest == node: continue
						my_neighbors = self.nodes[node].get_neighbors()
						list_dist = []
						for j in my_neighbors:
							if dest == j: continue
							distance = copyDvTable[j][j][dest] + self.hardLinks[node][j]
							if dest in self.nodes[j].next_hop:
								if self.nodes[j].next_hop[dest] == node: distance = float('inf')
							list_dist.append((self.hop_next[j][dest][1], j, distance))
						if len(list_dist) == 0: continue
						min_neigh = min(list_dist, key=lambda x:(x[2], x[0]))
						if min_neigh[2] < self.hardLinks[node][dest]:
							if self.nodes[node].dvTable[node][dest] != min_neigh[2]:
								self.nodes[node].next_hop[dest] = min_neigh[1]
								self.hop_next[node][dest] = (min_neigh[1], self.hop_next[min_neigh[1]][dest][1] + 1)
								if self.hop_next[min_neigh[1]][dest][1] + 1 > 100:
									count_to_inf = True
									break
								self.nodes[node].dvTable[node][dest] = min_neigh[2]
								converged = False
						else:
							if self.nodes[node].dvTable[node][dest] != self.hardLinks[node][dest]:
								self.nodes[node].dvTable[node][dest] = self.hardLinks[node][dest]
								self.hop_next[node][dest] = (dest, 1)
								del self.nodes[node].next_hop[dest]
								converged = False
				if count_to_inf:
					break;
				if len(topology_events) > 0: converged = False
				if DEBUG: self.debug_display()
		if count_to_inf == True:
			print("Count to infinity Instability at Round:", self.iteration)
		else:
			if output_format == 0:
				print("Round", self.iteration, "\n")
				for i in range(1, self.num_routers + 1):
					print(i, " ", end="")
					for j in range(1, self.num_routers + 1):
						print(self.hop_next[i][j]," ", end="")
					print("\n")
				print("\n")
			print("Convergence delay:", self.iteration - last_update, "rounds")
										


	################################

	# the basic protocol implementation
	def run_basic_protocol(self):
		if DEBUG: self.debug_display()
		converged = False
		last_update = 1
		count_to_inf = False
		while not converged:
			if output_format == 1:
				print("Round", self.iteration, "\n")
				for i in range(1, self.num_routers + 1):
					print(i, " ", end="")
					for j in range(1, self.num_routers + 1):
						print(self.hop_next[i][j]," ", end="")
					print("\n")
				print("\n")
			if count_to_inf: break
			converged = True
			if self.iteration in topology_events:
				links = topology_events[self.iteration]
				for link in links:
					removeflag = False
					from_node, to_node, distance = link
					if distance == -1: 
						distance = float('inf')
						removeflag = True
					if to_node in self.nodes[from_node].next_hop:
						del self.nodes[from_node].next_hop[to_node]
					if from_node in self.nodes[to_node].next_hop:
						del self.nodes[to_node].next_hop[from_node]
					self.hardLinks[from_node][to_node] = distance
					self.nodes[from_node].update(self.nodes[from_node], self.nodes[to_node], distance)
					self.hop_next[from_node][to_node] = (to_node, 1)
					self.hardLinks[to_node][from_node] = distance
					self.nodes[to_node].update(self.nodes[to_node], self.nodes[from_node], distance)
					self.hop_next[to_node][from_node] = (from_node, 1)
					self.nodes[from_node].update_neighbors(to_node, removeflag)
					self.nodes[to_node].update_neighbors(from_node, removeflag)
					converged = False
				last_update = self.iteration
				print("Updated Topology:\n")
				del topology_events[self.iteration]
			else:
				self.iteration += 1
				copyDvTable = {z: {i : {j : float('inf') for j in range(1, num_routers + 1)} for i in range(1, num_routers + 1)} for z in range(1, num_routers + 1)}
				for i in range (1, self.num_routers + 1):
					for j in range (1, self.num_routers + 1):
						for k in range(1, self.num_routers + 1):
							copyDvTable[i][j][k] = self.nodes[i].dvTable[j][k]

				for node in range(1, self.num_routers + 1):
					if count_to_inf: break
					for dest in range(1, self.num_routers + 1):
						if count_to_inf: break
						if dest == node: continue
						my_neighbors = self.nodes[node].get_neighbors()
						list_dist = []
						for j in my_neighbors:
							if dest == j: continue
							list_dist.append((self.hop_next[j][dest][1], j, copyDvTable[j][j][dest] + self.hardLinks[node][j]))
						if len(list_dist) == 0: continue
						min_neigh = min(list_dist, key=lambda x:(x[2], x[0]))
						if min_neigh[2] < self.hardLinks[node][dest]:
							if self.nodes[node].dvTable[node][dest] != min_neigh[2]:
								self.nodes[node].dvTable[node][dest] = min_neigh[2]
								self.hop_next[node][dest] = (min_neigh[1], self.hop_next[min_neigh[1]][dest][1] + 1)
								if self.hop_next[min_neigh[1]][dest][1] + 1 > 100:
									count_to_inf = True
								self.nodes[node].next_hop[dest] = min_neigh[1]
								converged = False
						else:
							if self.nodes[node].dvTable[node][dest] != self.hardLinks[node][dest]:
								self.nodes[node].dvTable[node][dest] = self.hardLinks[node][dest]
								self.hop_next[node][dest] = (dest, 1)
								del self.nodes[node].next_hop[dest]
								converged = False
				if count_to_inf:
					break
				if len(topology_events) > 0: converged = False
				if DEBUG: self.debug_display()
		if count_to_inf == True:
			print("Count to infinity Instability at Round:", self.iteration)
		else:
			if output_format == 0:
				print("Round", self.iteration, "\n")
				for i in range(1, self.num_routers + 1):
					print(i, " ", end="")
					for j in range(1, self.num_routers + 1):
						print(self.hop_next[i][j]," ", end="")
					print("\n")
				print("\n")
			print("Convergence delay:", self.iteration - last_update, "rounds")			

	# Split horizon implementation
	def split_horizon(self):
		if DEBUG: self.debug_display()
		converged = False
		count_to_inf = False
		last_update = 1
		while not converged and self.iteration < 100:
			if output_format == 1:
				print("Round", self.iteration, "\n")
				for i in range(1, self.num_routers + 1):
					print(i, " ", end="")
					for j in range(1, self.num_routers + 1):
						print(self.hop_next[i][j]," ", end="")
					print("\n")
				print("\n")
			converged = True
			if self.iteration in topology_events:
				links = topology_events[self.iteration]
				for link in links:
					from_node, to_node, distance = link
					removeflag = False
					if distance == -1: 
						distance = float('inf')
						removeflag = True
					if to_node in self.nodes[from_node].next_hop:
						del self.nodes[from_node].next_hop[to_node]
					if from_node in self.nodes[to_node].next_hop:
						del self.nodes[to_node].next_hop[from_node]
					self.nodes[from_node].update(self.nodes[from_node], self.nodes[to_node], distance)
					self.hop_next[from_node][to_node] = (to_node, 1)
					self.hardLinks[from_node][to_node] = distance
					self.hardLinks[to_node][from_node] = distance
					self.nodes[to_node].update(self.nodes[to_node], self.nodes[from_node], distance)
					self.nodes[from_node].update_neighbors(to_node, removeflag)
					self.nodes[to_node].update_neighbors(from_node, removeflag)
					self.hop_next[to_node][from_node] = (from_node, 1)
					converged = False
				last_update = self.iteration
				print("Updated Topology:\n")
				del topology_events[self.iteration]
			else:
				self.iteration += 1
				copyDvTable = {z: {i : {j : float('inf') for j in range(1, num_routers + 1)} for i in range(1, num_routers + 1)} for z in range(1, num_routers + 1)}
				for i in range (1, self.num_routers + 1):
					for j in range (1, self.num_routers + 1):
						for k in range(1, self.num_routers + 1):
							copyDvTable[i][j][k] = self.nodes[i].dvTable[j][k]

				for node in range(1, self.num_routers + 1):
					for dest in range(1, self.num_routers + 1):
						if dest == node: continue
						my_neighbors = self.nodes[node].get_neighbors()
						list_dist = []
						for j in my_neighbors:
							if dest == j: continue
							distance = copyDvTable[j][j][dest] + self.hardLinks[node][j]
							if dest in self.nodes[j].next_hop:
								if not self.nodes[j].next_hop[dest] == node:
									list_dist.append((self.hop_next[j][dest][1], j, distance))
							else:
								list_dist.append((self.hop_next[j][dest][1], j, distance))
						if len(list_dist) == 0: continue
						min_neigh = min(list_dist, key=lambda x:(x[2], x[1]))
						if min_neigh[2] < self.hardLinks[node][dest]:
							if self.nodes[node].dvTable[node][dest] != min_neigh[2]:
								self.nodes[node].next_hop[dest] = min_neigh[1]
								self.nodes[node].dvTable[node][dest] = min_neigh[2]
								self.hop_next[node][dest] = (min_neigh[1], self.hop_next[min_neigh[1]][dest][1] + 1)
								if self.hop_next[min_neigh[1]][dest][1] + 1 > 100:
									count_to_inf = True
								converged = False
						else:
							if self.nodes[node].dvTable[node][dest] != self.hardLinks[node][dest]:
								self.nodes[node].dvTable[node][dest] = self.hardLinks[node][dest]
								del self.nodes[node].next_hop[dest]
								self.hop_next[node][dest] = (dest, 1)
								converged = False
				if count_to_inf:
					break
				if len(topology_events) > 0: converged = False
				if DEBUG: self.debug_display()
		if count_to_inf == True:
			print("Count to infinity Instability at Round:", self.iteration)
		else:
			if output_format == 0:
				print("Round", self.iteration, "\n")
				for i in range(1, self.num_routers + 1):
					print(i, " ", end="")
					for j in range(1, self.num_routers + 1):
						print(self.hop_next[i][j]," ", end="")
					print("\n")
				print("\n")
			print("Convergence delay:", self.iteration - last_update, "rounds")


	def debug_display(self):
		print("Iteration", self.iteration)
		for i in range(1, num_routers + 1):
			print("\tRouter ", i, " port forwarding table:")
			for j in range(1, num_routers + 1):
				for k in range(1, num_routers + 1):
					print("\t", j, " - ", k, " : ", self.nodes[i].dvTable[j][k])


#############################3
# main method

if len(sys.argv) >= 3:
	if len(sys.argv) == 5 and sys.argv[4] == '-d':
		DEBUG = True

	num_routers, topology_inital = process_init_topology(sys.argv[1])
	topology_events = process_topology_events(sys.argv[2])

	# TODO: do something with the output_format
	output_format = int(sys.argv[3])
	algorithm = 1
	if len(sys.argv) < 4:
		algorithm = 0
	else:
		algorithm = int(sys.argv[4])

	# TODO: create three graphs for each algorithm and run them
	if algorithm == 0:
		print("Basic protocol\n")
		g1 = Graph(num_routers, topology_inital, topology_events)
		g1.run_basic_protocol()
		print("Poison Reverse\n")
		g2 = Graph(num_routers, topology_inital, topology_events)
		g2.poison_reverse()
		print("Split Horizon\n")
		g3 = Graph(num_routers, topology_inital, topology_events)
		g3.split_horizon()
	elif algorithm == 1:
		print("Basic protocol\n")
		g1 = Graph(num_routers, topology_inital, topology_events)
		g1.run_basic_protocol()
	elif algorithm == 2:
		print("Poison Reverse\n")
		g2 = Graph(num_routers, topology_inital, topology_events)
		g2.poison_reverse()
	else:
		print("Split Horizon\n")
		g3 = Graph(num_routers, topology_inital, topology_events)
		g3.split_horizon()
	
