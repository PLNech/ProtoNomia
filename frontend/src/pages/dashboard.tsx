import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { 
  Users, 
  TrendingUp, 
  FileText, 
  Clock, 
  Activity,
  Zap,
  Database,
  Settings,
  RefreshCw,
  Calendar
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Type definitions
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

type EconomicIndicators = {
  averageWealth: number;
  giniCoefficient: number;
  unemploymentRate: number;
  inflationRate: number;
  economicGrowth: number;
  resourceScarcity: number;
  marketStability: number;
  terraMarsTrade: number;
};

type RecentEvent = {
  id: string;
  timestamp: string;
  title: string;
  description: string;
  significance: number;
};

type HistoricalData = {
  tick: number;
  date: string;
  activeAgents: number;
  averageWealth: number;
  marketStability: number;
  interactions: number;
};

// Main component
const Dashboard = () => {
  const [simulation, setSimulation] = useState<SimulationStatus | null>(null);
  const [indicators, setIndicators] = useState<EconomicIndicators | null>(null);
  const [recentEvents, setRecentEvents] = useState<RecentEvent[]>([]);
  const [narrativeSummary, setNarrativeSummary] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([]);
  const webSocketRef = useRef<WebSocket | null>(null);

  // Fetch initial data
  useEffect(() => {
    fetchSimulationStatus();
    fetchEconomicIndicators();
    fetchRecentEvents();
    fetchNarrativeSummary();
    
    // Start with some sample historical data
    // In a real implementation, this would come from API
    const sampleData = Array.from({ length: 20 }, (_, i) => ({
      tick: i,
      date: new Date(Date.now() - (20 - i) * 3600000).toISOString(),
      activeAgents: 40 + Math.floor(Math.random() * 10),
      averageWealth: 800 + Math.floor(Math.random() * 200),
      marketStability: 0.4 + Math.random() * 0.3,
      interactions: 5 + Math.floor(Math.random() * 10)
    }));
    setHistoricalData(sampleData);
    
    return () => {
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
    };
  }, []);

  // Set up WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/current');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.event === 'tick_completed') {
          // Update simulation status
          fetchSimulationStatus();
          
          // Update historical data
          const newDataPoint: HistoricalData = {
            tick: data.data.tick,
            date: data.data.date,
            activeAgents: data.data.activeAgents,
            averageWealth: data.data.economicIndicators.averageWealth,
            marketStability: data.data.economicIndicators.marketStability,
            interactions: data.data.activeInteractions
          };
          
          setHistoricalData(prev => {
            const newData = [...prev, newDataPoint];
            if (newData.length > 50) { // Keep last 50 data points
              return newData.slice(newData.length - 50);
            }
            return newData;
          });
        } else if (data.event === 'narrative_event') {
          // Add to recent events
          setRecentEvents(prev => {
            const newEvent: RecentEvent = {
              id: data.data.id,
              timestamp: data.data.timestamp,
              title: data.data.title,
              description: data.data.description,
              significance: data.data.significance
            };
            
            const newEvents = [newEvent, ...prev];
            if (newEvents.length > 5) { // Keep last 5 events
              return newEvents.slice(0, 5);
            }
            return newEvents;
          });
          
          // Update narrative summary every 5 events
          if (recentEvents.length % 5 === 0) {
            fetchNarrativeSummary();
          }
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected, trying to reconnect...');
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };
      
      webSocketRef.current = ws;
    };
    
    connectWebSocket();
  }, [recentEvents.length]);

  const fetchSimulationStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulations/current');
      if (response.ok) {
        const data = await response.json();
        setSimulation(data);
        setIsRunning(true); // Assume running if we can fetch data
      }
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching simulation status:', error);
      setIsLoading(false);
    }
  };

  const fetchEconomicIndicators = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulations/current/economy');
      if (response.ok) {
        const data = await response.json();
        setIndicators({
          averageWealth: data.indicators.average_wealth,
          giniCoefficient: data.indicators.gini_coefficient,
          unemploymentRate: data.indicators.unemployment_rate || 0.1,
          inflationRate: data.indicators.inflation_rate || 0.02,
          economicGrowth: data.indicators.economic_growth || 0.03,
          resourceScarcity: data.indicators.resource_scarcity,
          marketStability: data.indicators.market_stability,
          terraMarsTrade: data.indicators.terra_mars_trade_balance || 0.5
        });
      }
    } catch (error) {
      console.error('Error fetching economic indicators:', error);
    }
  };

  const fetchRecentEvents = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulations/current/narrative/events?limit=5');
      if (response.ok) {
        const data = await response.json();
        setRecentEvents(data);
      }
    } catch (error) {
      console.error('Error fetching recent events:', error);
    }
  };

  const fetchNarrativeSummary = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulations/current/narrative/summary');
      if (response.ok) {
        const data = await response.json();
        setNarrativeSummary(data.summary);
      }
    } catch (error) {
      console.error('Error fetching narrative summary:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw size={24} className="animate-spin text-purple-500" />
          <span>Loading simulation data...</span>
        </div>
      </div>
    );
  }

  if (!simulation) {
    return (
      <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center">
        <h1 className="text-2xl mb-4">No simulation found</h1>
        <p className="mb-6">Create a simulation to view the dashboard</p>
        <Link href="/" className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-md">
          Go to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <Head>
        <title>Dashboard | ProtoNomia</title>
      </Head>

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 text-transparent bg-clip-text">
                ProtoNomia Dashboard
              </h1>
              <p className="text-gray-400">
                Mars Economy Simulation - Year 2993
              </p>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="text-right">
                <div className="flex items-center space-x-2 text-gray-300 mb-1">
                  <Clock size={16} />
                  <span>Simulation Time</span>
                </div>
                <div className="text-xl font-semibold text-cyan-400">
                  {new Date(simulation.currentDate).toLocaleString()}
                </div>
              </div>
              
              <Link href="/" className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-md flex items-center space-x-2">
                <Settings size={16} />
                <span>Controls</span>
              </Link>
            </div>
          </div>
        </header>

        {/* Status cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex items-center space-x-2 text-gray-400 mb-1">
              <Users size={16} />
              <span>Population</span>
            </div>
            <div className="text-3xl font-bold mb-1">{simulation.activeAgents}</div>
            <div className="text-sm text-gray-500">
              {simulation.deceasedAgents} deceased
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex items-center space-x-2 text-gray-400 mb-1">
              <Activity size={16} />
              <span>Interactions</span>
            </div>
            <div className="text-3xl font-bold mb-1">{simulation.activeInteractions}</div>
            <div className="text-sm text-gray-500">
              {simulation.narrativeEvents} narrative events
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex items-center space-x-2 text-gray-400 mb-1">
              <TrendingUp size={16} />
              <span>Economy</span>
            </div>
            <div className="text-3xl font-bold mb-1">
              {indicators?.averageWealth.toFixed(0) || '---'}
            </div>
            <div className="text-sm text-gray-500">
              Credits per capita
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex items-center space-x-2 text-gray-400 mb-1">
              <Zap size={16} />
              <span>Stability</span>
            </div>
            <div className="text-3xl font-bold mb-1">
              {(indicators?.marketStability * 100).toFixed(0) || '---'}%
            </div>
            <div className="text-sm text-gray-500">
              Market stability index
            </div>
          </div>
        </div>

        {/* Charts & Narrative */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Population chart */}
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Population & Economy Trends</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={historicalData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis 
                    dataKey="tick" 
                    stroke="#888"
                    label={{ value: 'Simulation Tick', position: 'insideBottomRight', offset: -10, fill: '#888' }}
                  />
                  <YAxis stroke="#888" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#222', borderColor: '#555' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="activeAgents" 
                    name="Population" 
                    stroke="#8884d8" 
                    activeDot={{ r: 8 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="averageWealth" 
                    name="Avg. Wealth" 
                    stroke="#82ca9d" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="interactions" 
                    name="Interactions" 
                    stroke="#ffc658" 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Economic indicators */}
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <h2 className="text-xl font-semibold mb-4">Economic Indicators</h2>
            {indicators ? (
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400">Gini Coefficient</span>
                    <span className="font-medium">
                      {indicators.giniCoefficient.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-blue-500 h-full" 
                      style={{ width: `${indicators.giniCoefficient * 100}%` }}
                    />
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400">Resource Scarcity</span>
                    <span className="font-medium">
                      {indicators.resourceScarcity.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${indicators.resourceScarcity > 0.7 ? 'bg-red-500' : 'bg-yellow-500'}`}
                      style={{ width: `${indicators.resourceScarcity * 100}%` }}
                    />
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400">Terra-Mars Trade</span>
                    <span className="font-medium">
                      {indicators.terraMarsTrade > 0 ? '+' : ''}{indicators.terraMarsTrade.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${indicators.terraMarsTrade > 0 ? 'bg-green-500' : 'bg-red-500'}`}
                      style={{ 
                        width: `${Math.abs(indicators.terraMarsTrade) * 100}%`,
                        marginLeft: indicators.terraMarsTrade < 0 ? 0 : '50%',
                        marginRight: indicators.terraMarsTrade > 0 ? 0 : '50%'
                      }}
                    />
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400">Market Stability</span>
                    <span className="font-medium">
                      {indicators.marketStability.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${
                        indicators.marketStability > 0.7 ? 'bg-green-500' : 
                        indicators.marketStability > 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${indicators.marketStability * 100}%` }}
                    />
                  </div>
                </div>
                
                <div className="pt-2">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-gray-400 text-sm mb-1">Growth Rate</div>
                      <div className={`text-lg font-semibold ${
                        indicators.economicGrowth > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {indicators.economicGrowth > 0 ? '+' : ''}{(indicators.economicGrowth * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-sm mb-1">Inflation</div>
                      <div className={`text-lg font-semibold ${
                        indicators.inflationRate > 0.05 ? 'text-red-400' : 'text-green-400'
                      }`}>
                        {(indicators.inflationRate * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-gray-500 py-4 text-center">
                Economic data unavailable
              </div>
            )}
          </div>
        </div>

        {/* Recent events & Narrative */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent events */}
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Recent Events</h2>
              <Link href="/narrative" className="text-purple-400 hover:text-purple-300 text-sm flex items-center">
                <span>View all</span>
                <span className="ml-1">→</span>
              </Link>
            </div>
            
            {recentEvents.length > 0 ? (
              <div className="space-y-4">
                {recentEvents.map((event) => (
                  <div key={event.id} className="border-l-2 border-purple-600 pl-4 py-1">
                    <div className="flex items-center text-sm text-gray-400 mb-1">
                      <Calendar size={14} className="mr-1" />
                      <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                      <span className="ml-2 px-2 py-0.5 bg-gray-800 rounded-full text-xs">
                        Significance: {event.significance.toFixed(1)}
                      </span>
                    </div>
                    <h3 className="font-medium text-purple-300 mb-1">{event.title}</h3>
                    <p className="text-sm text-gray-300">{event.description}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-gray-500 py-4 text-center">
                No events yet
              </div>
            )}
          </div>
          
          {/* Narrative summary */}
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg lg:col-span-2">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Narrative Summary</h2>
              <Link href="/narrative" className="text-cyan-400 hover:text-cyan-300 text-sm flex items-center">
                <span>Full story</span>
                <span className="ml-1">→</span>
              </Link>
            </div>
            
            {narrativeSummary ? (
              <div className="prose prose-invert prose-sm max-w-none">
                <p className="text-gray-300 leading-relaxed">{narrativeSummary}</p>
              </div>
            ) : (
              <div className="text-gray-500 py-4 text-center">
                Narrative still developing...
              </div>
            )}
          </div>
        </div>

        {/* Navigation footer */}
        <div className="mt-8 pt-6 border-t border-gray-800 grid grid-cols-3 gap-4">
          <Link href="/agents" className="flex items-center text-gray-400 hover:text-white">
            <Users size={18} className="mr-2" />
            <span>Agent Population</span>
          </Link>
          
          <Link href="/economy" className="flex items-center justify-center text-gray-400 hover:text-white">
            <TrendingUp size={18} className="mr-2" />
            <span>Economic Data</span>
          </Link>
          
          <Link href="/narrative" className="flex items-center justify-end text-gray-400 hover:text-white">
            <FileText size={18} className="mr-2" />
            <span>Narrative Chronicle</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;