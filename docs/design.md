# Design MVP

ProtoNomia: a fun simulation that allows us to assess/illustrate/benchmark various economic theory principles.
e.g. testing cooperation vs defection in iterated prisoner's dillemma conditions

The project must be scientifically sound, yet entertaining and didactic and never boring.

I want to run the multi agent simulation in python
but I would love to have the frontend a nice next.js app with realtime dashboard analytics etc
Also we want this to be embedded in a kind of realistic economy to make it more narrative interesting. Setting is Cyberpunk, 2993, on Mars, where humans have a first solid implantation out of Terra, transplanetary economy's mostly digital and service-based, selling software and entertainment to Terra against material and goods that the local blooming industry doesn't already provide.
There should be a Narrator which produces a story from the Agents' interactions.
Hence they must birth, live, age, and die, to ensure a nice cycle.
Implement self-correcting population control mechanics.
MVP needs basic lifecycle, population init, narrator, and a couple econ interactions. 

Wait we forgot a big detail! Agents are LLM based. We are gonna send them a payload via ollama through a requests POST with timeout=5s and retry3 else agent passes this round, where the agent is told potential interaction parters, log of proposed interactions by others, can send accept/negotiate/reject response interactions, can choose strategies between resting/searching for job/working/buying goods/etc. Think about the above simulation models and interactions to define an action ontology and pydantic model, then use it in the prompt for the agents.

Example, we use this great small fast gemma3:1b check this curl prototype:
ollama run gemma3:1b "You are an agent in a simulated economy. You currently have 5 dollars. You have 100/100 full stomach, are 100/100 rested. Your neighbors are [agent1, agent3, agent4]. You currently have: no job. Your possible interactions are REST/OFFER(what:str, against_what:str)/NEGOTIATE(offer_id:int, message:str)/ACCEPT(offer_id:int)/REJECT(offer_id:int)/SEARCH_JOB()/WORK(job_id)/BUY(desired_item:str). The turn is 122/200. What do youchoose to do? Think in max 20 words then return CHOICE:{'type':TYPE, 'extra':{}}. No comment after CHOICE only your choice in valid json." { 'type': "SEARCH_JOB", 'extra': "Look for available positions to earn more.'}
But improve my prompt add few shots constrain it more add Instructor for the pydantic modeling.