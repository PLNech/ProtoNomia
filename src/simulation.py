class Simulation:
    def __init__(self):
        super().__init__()
        self.state = None # TODO Implement a SimulationState class:
        """
        TODO SimulationState:
        market: GlobalMarket 
        agents: List[Agent]
        day: int
        ...
        """


    def describe(self):
        """Returns a text description of the state of the simulation, comprehensive for agents to choose the best action on this info only."""
        pass

    def run(self):
        # Runs the simulation:
        # For each day, one tick
        # StepActions: Ask each Agent, given describe(self.state) , what action to do (the agent will complete the simulation description with their own internal state to choose action) and store them
        # StepConsequences: apply one by one the agents' actions, updating their resources and states accordingly, updating the global market accordingly, in order:
            ## Action.REST: Gives 0.2 of AgentNeed.rest, max at 1
            ## Action.WORK: Adds 100 credits to agent.credits
            ## Action.SELL: Sells item with index from agent.goods and chosen price, e.g. SELL(0, 100) to sell agent.goods[0] for 100 credits
            ## Action.BUY: Buy from the GlobalMarket, triggers a Negotiator.negotiate(agent_1, agent_2, good) call - for now MVP this accepts at exact price or rejects if lacking credits.
            ## Action.HARVEST: Harvest shrooms from a colony farm, get food for your time -> agent.goods.append(Good of type FOOD, value random 0.2-0.8, name=one of 10 shroom names (5 real mushroom names + 5 new martian shroom names))
            ## Action.CRAFT: Invent a new item, you can send optional materials:float credits to make it more likely to be high quality, logarithmic formula (so you can go from average 0.5 to average 0.75 with a few bucks, but to ensure >0.99 you need to spend quite a lot more) - random name with a 3parts invention-o-matic name generator
        # StepHunger: lower all agent.needs counters by 0.01
        # StepDeath: kill all agents with any needs <=0, store metadata for agent death day/causes in the simulation
        # StepStop: when everybody died or more than --until days have passed, stop the simulation and return
        # StepNarration: uses the Narrator to generate a NarrationResponse for this day

        pass # Runs the simulation one tick at a time, calling narrator after each round

if __name__ == '__main__':
    # TODO: Add argparse for key simulation parameters such as --population and --until
    # The simulation must run in a console, printing for each day:
    # The agent decisions
    # The narrator daily summary
    s = Simulation()
    s.run()