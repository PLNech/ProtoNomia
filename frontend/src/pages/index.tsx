// frontend/protonomia-ui/src/pages/index.tsx

import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { 
  ChevronRight, 
  Settings, 
  Play, 
  Pause, 
  SkipForward,
  Users,
  TrendingUp,
  FileText,
  Home
} from 'lucide-react';

type SimulationStatus = {
  id: string;
  name: string;
  currentTick: number;
  currentDate: string;
  activeAgents: number;
  deceasedAgents: number;
  activeInteractions: number;
  narrativeEvents: number;
};

const Home = () => {
  const router = useRouter();
  const [simulation, setSimulation] = useState<SimulationStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [simulationSpeed, setSimulationSpeed] = useState(1.0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check if a simulation exists on load
    fetchSimulationStatus();
  }, []);

  const fetchSimulationStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulations/current');
      if (response.ok) {
        const data = await response.json();
        setSimulation(data);
      }
    } catch (error) {
      console.error('Error fetching simulation status:', error);
    }
  };

  const createSimulation = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/simulations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'ProtoNomia Mars',
          initial_population: 50,
          resource_scarcity: 0.6,
          technological_level: 0.8,
          narrative_verbosity: 4,
          agent_model: 'gemma:4b',
          narrator_model: 'gemma:4b'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSimulation(data);
        router.push('/dashboard');
      }
    } catch (error) {
      console.error('Error creating simulation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startSimulation = async () => {
    try {
      const response = await fetch(`http://localhost:8000/simulations/current/start?speed=${simulationSpeed}`, {
        method: 'POST',
      });
      if (response.ok) {
        setIsRunning(true);
      }
    } catch (error) {
      console.error('Error starting simulation:', error);
    }
  };

  const stopSimulation = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulations/current/stop', {
        method: 'POST',
      });
      if (response.ok) {
        setIsRunning(false);
      }
    } catch (error) {
      console.error('Error stopping simulation:', error);
    }
  };

  const runSingleTick = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulations/current/tick', {
        method: 'POST',
      });
      if (response.ok) {
        fetchSimulationStatus();
      }
    } catch (error) {
      console.error('Error running tick:', error);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <Head>
        <title>ProtoNomia - Cyberpunk Mars Economic Simulation</title>
        <meta name="description" content="Cyberpunk Mars economic game theory simulation" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        <div className="flex flex-col items-center justify-center min-h-[80vh]">
          <h1 className="text-6xl font-bold mb-8 text-center bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 text-transparent bg-clip-text">
            ProtoNomia
          </h1>
          <p className="text-2xl text-center mb-8 text-gray-300">
            Cyberpunk Mars Economic Simulation - Year 2993
          </p>

          {simulation ? (
            <div className="w-full max-w-2xl">
              <div className="bg-gray-900 p-6 rounded-lg shadow-lg mb-6">
                <h2 className="text-xl font-semibold mb-4 text-cyan-400">Current Simulation</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-gray-400">Name</p>
                    <p className="font-medium">{simulation.name}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Date</p>
                    <p className="font-medium">{new Date(simulation.currentDate).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Active Agents</p>
                    <p className="font-medium">{simulation.activeAgents}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Current Tick</p>
                    <p className="font-medium">{simulation.currentTick}</p>
                  </div>
                </div>
                
                <div className="mt-6 flex space-x-4">
                  <button 
                    onClick={isRunning ? stopSimulation : startSimulation}
                    className={`px-4 py-2 rounded-md flex items-center space-x-2
                      ${isRunning 
                        ? 'bg-red-600 hover:bg-red-700' 
                        : 'bg-green-600 hover:bg-green-700'}`}
                  >
                    {isRunning ? (
                      <>
                        <Pause size={16} />
                        <span>Pause</span>
                      </>
                    ) : (
                      <>
                        <Play size={16} />
                        <span>Start</span>
                      </>
                    )}
                  </button>
                  
                  <button 
                    onClick={runSingleTick}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md flex items-center space-x-2"
                    disabled={isRunning}
                  >
                    <SkipForward size={16} />
                    <span>Single Tick</span>
                  </button>
                </div>
                
                <div className="mt-6">
                  <label className="block text-gray-400 mb-2">Simulation Speed</label>
                  <input 
                    type="range" 
                    min="0.1" 
                    max="5" 
                    step="0.1" 
                    value={simulationSpeed}
                    onChange={(e) => setSimulationSpeed(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-gray-500">
                    <span>Fast</span>
                    <span>{simulationSpeed.toFixed(1)}s</span>
                    <span>Slow</span>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <Link href="/dashboard" className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg flex items-center">
                  <div className="bg-purple-900 p-2 rounded-md mr-3">
                    <Home size={20} />
                  </div>
                  <div>
                    <h3 className="font-medium">Dashboard</h3>
                    <p className="text-sm text-gray-400">Main overview</p>
                  </div>
                  <ChevronRight size={16} className="ml-auto text-gray-500" />
                </Link>
                
                <Link href="/agents" className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg flex items-center">
                  <div className="bg-blue-900 p-2 rounded-md mr-3">
                    <Users size={20} />
                  </div>
                  <div>
                    <h3 className="font-medium">Agents</h3>
                    <p className="text-sm text-gray-400">Population data</p>
                  </div>
                  <ChevronRight size={16} className="ml-auto text-gray-500" />
                </Link>
                
                <Link href="/economy" className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg flex items-center">
                  <div className="bg-green-900 p-2 rounded-md mr-3">
                    <TrendingUp size={20} />
                  </div>
                  <div>
                    <h3 className="font-medium">Economy</h3>
                    <p className="text-sm text-gray-400">Market & resources</p>
                  </div>
                  <ChevronRight size={16} className="ml-auto text-gray-500" />
                </Link>
                
                <Link href="/narrative" className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg flex items-center">
                  <div className="bg-red-900 p-2 rounded-md mr-3">
                    <FileText size={20} />
                  </div>
                  <div>
                    <h3 className="font-medium">Narrative</h3>
                    <p className="text-sm text-gray-400">Simulation story</p>
                  </div>
                  <ChevronRight size={16} className="ml-auto text-gray-500" />
                </Link>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <p className="mb-6 text-gray-400">No active simulation. Create one to begin.</p>
              <button
                onClick={createSimulation}
                disabled={isLoading}
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-md font-medium flex items-center mx-auto"
              >
                {isLoading ? 'Creating...' : 'Create New Simulation'}
              </button>
            </div>
          )}
        </div>
      </main>

      <footer className="container mx-auto px-4 py-6 border-t border-gray-800 mt-8">
        <p className="text-center text-gray-500">
          ProtoNomia - Cyberpunk Mars Economic Simulation
        </p>
      </footer>
    </div>
  );
};

export default Home;