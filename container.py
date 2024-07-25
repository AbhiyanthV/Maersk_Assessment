import simpy
import random

# Constants
AVG_TIME_BETWEEN_VESSELS = 5 * 60 # in minute 
NUM_CONTAINERS_PER_VESSEL = 150  
TIME_TO_MOVE_CONTAINER = 3  # in minutes
TIME_TO_TRANSPORT_CONTAINER = 6  # in minutes
SIMULATION_TIME = 24 * 60  

class ContainerTerminal:
    def __init__(self, env):
        self.env = env
        self.berths = simpy.Resource(env, capacity=2)
        self.cranes = {1: simpy.Resource(env, capacity=1), 2: simpy.Resource(env, capacity=1)}
        self.trucks = simpy.Resource(env, capacity=3)
        self.truck_queue = list(range(1, 4))  # Truck IDs 1, 2, 3 for better clarity 

    def arrive(self, vessel_name):
        # Simulate vessel arrival time

        yield self.env.timeout(random.expovariate(1 / AVG_TIME_BETWEEN_VESSELS))
        print(f"{vessel_name} arrives to berth at time {self.env.now:7.4f} minutes")
        
        #if no berth is available
        if len(self.berths.queue) > 0:
            print(f"{vessel_name} is waiting for a berth at time {self.env.now:7.4f} minutes")
        
        # Requesting a berth
        berth_req = self.berths.request()
        yield berth_req
        berth_number = self.berths.count
        print(f"{vessel_name} berths at Berth_{berth_number} at time {self.env.now:7.4f} minutes")
        
        # Starting the unloading  the container process
        yield self.env.process(self.unload(vessel_name, berth_number))
        self.berths.release(berth_req)
        print(f"{vessel_name} leaves Berth_{berth_number} at {self.env.now:7.4f} minutes")

    def unload(self, vessel_name, berth_number):
        crane = self.cranes[berth_number]  

        for i in range(NUM_CONTAINERS_PER_VESSEL):
            # Requesting  the corresponding crane
            crane_req = crane.request()
            yield crane_req
            crane_number = berth_number 
            print(f'Crane {crane_number} starts moving container {i+1} from {vessel_name} at {self.env.now:7.4f} minutes')
            yield self.env.timeout(TIME_TO_MOVE_CONTAINER)
            

            # Request a truck and immediately start transportation
            if self.truck_queue:
                truck_id = self.truck_queue.pop(0)  # Get the next available truck ID
                truck_req = self.trucks.request()
                yield truck_req
                print(f'Crane {crane_number} finished moving container {i+1} from {vessel_name} to Truck {truck_id} at {self.env.now:7.4f} minutes')
                print(f'Truck {truck_id} starts transporting container {i+1} from {vessel_name} at {self.env.now:7.4f} minutes')
                self.env.process(self.transport_container(truck_req, truck_id, i+1, vessel_name))
            else:
                print(f"No truck available for Crane {crane_number} at {vessel_name} at {self.env.now:7.4f} minutes")
                yield self.env.timeout(1)  # Wait for a short time before retrying

            # Release the crane
            crane.release(crane_req)
            yield self.env.timeout(0)  # Ensures next crane operation can start immediately

        print(f"All containers are successfully unloaded from {vessel_name} at Berth_{berth_number} at time {self.env.now:7.4f} minutes")

    def transport_container(self, truck_req, truck_id, container_number, vessel_name):
        yield self.env.timeout(TIME_TO_TRANSPORT_CONTAINER)
        print(f'Truck {truck_id} finished transporting container {container_number} from {vessel_name} at {self.env.now:7.4f} minutes')
        self.trucks.release(truck_req)
        self.truck_queue.append(truck_id)  # Return the truck to the queue

def vessel_generator(env, terminal):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1 / AVG_TIME_BETWEEN_VESSELS))
        env.process(terminal.arrive(f"Vessel {i+1}"))
        i += 1

# Setup and start the simulation
print('Container Terminal Simulation')
env = simpy.Environment()
terminal = ContainerTerminal(env)
env.process(vessel_generator(env, terminal))
env.run(until=SIMULATION_TIME)
