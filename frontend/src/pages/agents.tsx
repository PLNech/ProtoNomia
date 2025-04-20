import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { 
  Users, 
  Home, 
  Filter, 
  Search, 
  RefreshCw,
  ArrowUpDown,
  UserCheck,
  UserX,
  Heart,
  Brain,
  Shield,
  Star,
  Award
} from 'lucide-react';

// Type definitions
type Agent = {
  id: string;
  name: string;
  type: string;
  faction: string;
  age_days: number;
  is_alive: boolean;
  location: string;
  personality: {
    cooperativeness: number;
    risk_tolerance: number;
    fairness_preference: number;
    altruism: number;
    rationality: number;
    long_term_orientation: number;
  };
  needs: {
    subsistence: number;
    security: number;
    social: number;
    esteem: number;
    self_actualization: number;
  };
  resources: Array<{
    type: string;
    amount: number;
  }>;
  background: string;
};

// Main component
const AgentsPage = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFaction, setSelectedFaction] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [showDeceased, setShowDeceased] = useState(false);
  const [sortBy, setSortBy] = useState<string>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [agentStats, setAgentStats] = useState({
    total: 0,
    alive: 0,
    deceased: 0,
    factions: {} as Record<string, number>,
    types: {} as Record<string, number>
  });

  // Fetch agents data
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(
          `http://localhost:8000/simulations/current/agents?alive_only=${!showDeceased}&limit=200`
        );
        
        if (response.ok) {
          const data = await response.json();
          setAgents(data);
          
          // Calculate stats
          const stats = {
            total: data.length,
            alive: data.filter((a: Agent) => a.is_alive).length,
            deceased: data.filter((a: Agent) => !a.is_alive).length,
            factions: {} as Record<string, number>,
            types: {} as Record<string, number>
          };
          
          data.forEach((agent: Agent) => {
            stats.factions[agent.faction] = (stats.factions[agent.faction] || 0) + 1;
            stats.types[agent.type] = (stats.types[agent.type] || 0) + 1;
          });
          
          setAgentStats(stats);
        }
      } catch (error) {
        console.error('Error fetching agents:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchAgents();
  }, [showDeceased]);

  // Apply filters and sorting when data or filters change
  useEffect(() => {
    let result = [...agents];
    
    // Apply faction filter
    if (selectedFaction !== 'all') {
      result = result.filter(agent => agent.faction === selectedFaction);
    }
    
    // Apply type filter
    if (selectedType !== 'all') {
      result = result.filter(agent => agent.type === selectedType);
    }
    
    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(agent => 
        agent.name.toLowerCase().includes(query) || 
        agent.location.toLowerCase().includes(query)
      );
    }
    
    // Apply sort
    result.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'age':
          comparison = a.age_days - b.age_days;
          break;
        case 'faction':
          comparison = a.faction.localeCompare(b.faction);
          break;
        case 'wealth':
          const aWealth = a.resources.find(r => r.type === 'credits')?.amount || 0;
          const bWealth = b.resources.find(r => r.type === 'credits')?.amount || 0;
          comparison = aWealth - bWealth;
          break;
        default:
          comparison = 0;
      }
      
      return sortDirection === 'asc' ? comparison : -comparison;
    });
    
    setFilteredAgents(result);
  }, [agents, selectedFaction, selectedType, searchQuery, sortBy, sortDirection]);

  // Handle sort toggle
  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDirection('asc');
    }
  };

  // Handle agent selection
  const handleAgentClick = (agent: Agent) => {
    setSelectedAgent(agent);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw size={24} className="animate-spin text-purple-500" />
          <span>Loading agents data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <Head>
        <title>Agent Population | ProtoNomia</title>
      </Head>

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 text-transparent bg-clip-text">
                Mars Population
              </h1>
              <p className="text-gray-400">
                Agents in the ProtoNomia Simulation
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link href="/dashboard" className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-md flex items-center space-x-2">
                <Home size={16} />
                <span>Dashboard</span>
              </Link>
            </div>
          </div>
        </header>

        {/* Stats cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900 rounded-lg p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-400 text-sm mb-1">Total Agents</div>
                <div className="text-2xl font-bold">{agentStats.total}</div>
              </div>
              <Users size={24} className="text-purple-400" />
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-400 text-sm mb-1">Living</div>
                <div className="text-2xl font-bold">{agentStats.alive}</div>
              </div>
              <UserCheck size={24} className="text-green-400" />
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-400 text-sm mb-1">Deceased</div>
                <div className="text-2xl font-bold">{agentStats.deceased}</div>
              </div>
              <UserX size={24} className="text-red-400" />
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-400 text-sm mb-1">Locations</div>
                <div className="text-2xl font-bold">
                  {new Set(agents.map(a => a.location)).size}
                </div>
              </div>
              <Home size={24} className="text-blue-400" />
            </div>
          </div>
        </div>

        {/* Filters and content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar / Filters */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
              <h2 className="text-lg font-semibold mb-4 flex items-center">
                <Filter size={16} className="mr-2" />
                <span>Filters</span>
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Search</label>
                  <div className="relative">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Name or location..."
                      className="w-full bg-gray-800 text-white pl-10 pr-4 py-2 rounded-md focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Faction</label>
                  <select
                    value={selectedFaction}
                    onChange={(e) => setSelectedFaction(e.target.value)}
                    className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-1 focus:ring-purple-500"
                  >
                    <option value="all">All Factions</option>
                    {Object.keys(agentStats.factions).map(faction => (
                      <option key={faction} value={faction}>
                        {faction.replace('_', ' ')} ({agentStats.factions[faction]})
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Type</label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-1 focus:ring-purple-500"
                  >
                    <option value="all">All Types</option>
                    {Object.keys(agentStats.types).map(type => (
                      <option key={type} value={type}>
                        {type.replace('_', ' ')} ({agentStats.types[type]})
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="pt-2">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showDeceased}
                      onChange={() => setShowDeceased(!showDeceased)}
                      className="w-4 h-4 bg-gray-800 border-gray-600 rounded focus:ring-purple-500"
                    />
                    <span className="text-gray-300">Include deceased</span>
                  </label>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
              <h2 className="text-lg font-semibold mb-4">Faction Distribution</h2>
              <div className="space-y-3">
                {Object.entries(agentStats.factions).map(([faction, count]) => (
                  <div key={faction}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-300">
                        {faction.replace('_', ' ')}
                      </span>
                      <span className="text-sm font-medium">
                        {count} ({Math.round(count / agentStats.total * 100)}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${
                          faction === 'terra_corporation' ? 'bg-blue-500' :
                          faction === 'mars_native' ? 'bg-red-500' :
                          faction === 'independent' ? 'bg-yellow-500' :
                          faction === 'government' ? 'bg-green-500' :
                          'bg-purple-500'
                        }`}
                        style={{ width: `${(count / agentStats.total) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Main content / Agent List and Details */}
          <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Agent List */}
            <div className="md:col-span-1 bg-gray-900 rounded-lg shadow-lg overflow-hidden">
              <div className="p-4 border-b border-gray-800">
                <h2 className="text-lg font-semibold">Agents</h2>
                <p className="text-sm text-gray-400">
                  {filteredAgents.length} agents found
                </p>
              </div>
              
              <div className="p-4 border-b border-gray-800">
                <div className="flex items-center space-x-2 text-sm">
                  <button 
                    onClick={() => handleSort('name')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded ${
                      sortBy === 'name' ? 'bg-gray-800' : 'hover:bg-gray-800'
                    }`}
                  >
                    <span>Name</span>
                    {sortBy === 'name' && (
                      <ArrowUpDown size={12} className="text-purple-400" />
                    )}
                  </button>
                  
                  <button 
                    onClick={() => handleSort('faction')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded ${
                      sortBy === 'faction' ? 'bg-gray-800' : 'hover:bg-gray-800'
                    }`}
                  >
                    <span>Faction</span>
                    {sortBy === 'faction' && (
                      <ArrowUpDown size={12} className="text-purple-400" />
                    )}
                  </button>
                  
                  <button 
                    onClick={() => handleSort('age')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded ${
                      sortBy === 'age' ? 'bg-gray-800' : 'hover:bg-gray-800'
                    }`}
                  >
                    <span>Age</span>
                    {sortBy === 'age' && (
                      <ArrowUpDown size={12} className="text-purple-400" />
                    )}
                  </button>
                  
                  <button 
                    onClick={() => handleSort('wealth')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded ${
                      sortBy === 'wealth' ? 'bg-gray-800' : 'hover:bg-gray-800'
                    }`}
                  >
                    <span>Wealth</span>
                    {sortBy === 'wealth' && (
                      <ArrowUpDown size={12} className="text-purple-400" />
                    )}
                  </button>
                </div>
              </div>
              
              <div className="overflow-y-auto" style={{ maxHeight: '600px' }}>
                {filteredAgents.length > 0 ? (
                  <div className="divide-y divide-gray-800">
                    {filteredAgents.map((agent) => (
                      <div 
                        key={agent.id}
                        onClick={() => handleAgentClick(agent)}
                        className={`p-3 cursor-pointer transition-colors hover:bg-gray-800 ${
                          selectedAgent?.id === agent.id ? 'bg-gray-800 border-l-4 border-purple-500' : ''
                        } ${
                          !agent.is_alive ? 'opacity-60' : ''
                        }`}
                      >
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-2 ${
                            agent.faction === 'terra_corporation' ? 'bg-blue-500' :
                            agent.faction === 'mars_native' ? 'bg-red-500' :
                            agent.faction === 'independent' ? 'bg-yellow-500' :
                            agent.faction === 'government' ? 'bg-green-500' :
                            'bg-purple-500'
                          }`} />
                          <span className="font-medium">{agent.name}</span>
                          {!agent.is_alive && (
                            <span className="ml-2 px-2 py-0.5 bg-red-900 rounded-full text-xs">
                              Deceased
                            </span>
                          )}
                        </div>
                        
                        <div className="mt-1 text-sm text-gray-400 flex justify-between">
                          <span>{agent.type.replace('_', ' ')}</span>
                          <span>{agent.age_days} days old</span>
                        </div>
                        
                        <div className="mt-1 text-xs text-gray-500">
                          Location: {agent.location}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 text-center text-gray-500">
                    No agents match your filters
                  </div>
                )}
              </div>
            </div>
            
            {/* Agent Details */}
            <div className="md:col-span-2">
              {selectedAgent ? (
                <div className="bg-gray-900 rounded-lg shadow-lg p-6">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h2 className="text-2xl font-bold text-white">{selectedAgent.name}</h2>
                      <div className="flex items-center mt-1">
                        <div className={`w-3 h-3 rounded-full mr-2 ${
                          selectedAgent.faction === 'terra_corporation' ? 'bg-blue-500' :
                          selectedAgent.faction === 'mars_native' ? 'bg-red-500' :
                          selectedAgent.faction === 'independent' ? 'bg-yellow-500' :
                          selectedAgent.faction === 'government' ? 'bg-green-500' :
                          'bg-purple-500'
                        }`} />
                        <span className="text-gray-300">{selectedAgent.faction.replace('_', ' ')}</span>
                        <span className="mx-2">•</span>
                        <span className="text-gray-300">{selectedAgent.type.replace('_', ' ')}</span>
                      </div>
                    </div>
                    
                    {!selectedAgent.is_alive && (
                      <div className="px-3 py-1 bg-red-900 text-white rounded-md text-sm">
                        Deceased
                      </div>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Left column */}
                    <div>
                      <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-3 flex items-center">
                          <Award size={16} className="mr-2 text-yellow-400" />
                          Background
                        </h3>
                        <p className="text-gray-300 text-sm leading-relaxed">
                          {selectedAgent.background}
                        </p>
                      </div>
                      
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center">
                          <Brain size={16} className="mr-2 text-purple-400" />
                          Personality
                        </h3>
                        <div className="space-y-2">
                          {Object.entries(selectedAgent.personality).map(([trait, value]) => (
                            <div key={trait}>
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-sm text-gray-400 capitalize">
                                  {trait.replace('_', ' ')}
                                </span>
                                <span className="text-sm">{value.toFixed(2)}</span>
                              </div>
                              <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                                <div 
                                  className="bg-purple-500 h-full"
                                  style={{ width: `${value * 100}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    {/* Right column */}
                    <div>
                      <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-3 flex items-center">
                          <Heart size={16} className="mr-2 text-red-400" />
                          Needs
                        </h3>
                        <div className="space-y-2">
                          {Object.entries(selectedAgent.needs).map(([need, value]) => (
                            <div key={need}>
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-sm text-gray-400 capitalize">
                                  {need}
                                </span>
                                <span className="text-sm">{value.toFixed(2)}</span>
                              </div>
                              <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full ${
                                    value > 0.7 ? 'bg-green-500' :
                                    value > 0.3 ? 'bg-yellow-500' :
                                    'bg-red-500'
                                  }`}
                                  style={{ width: `${value * 100}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center">
                          <Database size={16} className="mr-2 text-blue-400" />
                          Resources
                        </h3>
                        <div className="bg-gray-800 rounded-lg p-4">
                          <div className="space-y-3">
                            {selectedAgent.resources.map((resource) => (
                              <div key={resource.type} className="flex justify-between items-center">
                                <span className="text-gray-300 capitalize">
                                  {resource.type.replace('_', ' ')}
                                </span>
                                <span className="font-medium">
                                  {resource.amount.toFixed(1)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-6 pt-6 border-t border-gray-800">
                    <div className="flex items-center justify-between">
                      <div className="text-gray-400 text-sm">
                        <span>ID: {selectedAgent.id.substring(0, 8)}...</span>
                        <span className="mx-2">•</span>
                        <span>Age: {selectedAgent.age_days} days</span>
                        <span className="mx-2">•</span>
                        <span>Location: {selectedAgent.location}</span>
                      </div>
                      
                      <button className="text-purple-400 hover:text-purple-300 text-sm">
                        View Interactions →
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-900 rounded-lg shadow-lg p-6 h-full flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <Users size={48} className="mx-auto mb-4 opacity-50" />
                    <p>Select an agent to view details</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentsPage;