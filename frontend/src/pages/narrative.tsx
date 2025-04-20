import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { 
  Home, 
  FileText, 
  Calendar, 
  Clock, 
  BookOpen,
  RefreshCw,
  Filter,
  Tag,
  Star,
  Users,
  ArrowLeft,
  ArrowRight,
  MessageSquare,
  BookMarked
} from 'lucide-react';

// Type definitions
type NarrativeEvent = {
  id: string;
  timestamp: string;
  title: string;
  description: string;
  agents_involved: string[];
  significance: number;
  tags: string[];
};

type NarrativeArc = {
  id: string;
  title: string;
  description: string;
  agents_involved: string[];
  start_time: string;
  end_time?: string;
  is_complete: boolean;
  events: string[];
};

type Agent = {
  id: string;
  name: string;
  faction: string;
};

// Main component
const NarrativePage = () => {
  const [events, setEvents] = useState<NarrativeEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<NarrativeEvent[]>([]);
  const [narrativeArcs, setNarrativeArcs] = useState<NarrativeArc[]>([]);
  const [narrativeSummary, setNarrativeSummary] = useState<string>('');
  const [agents, setAgents] = useState<Record<string, Agent>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<NarrativeEvent | null>(null);
  const [selectedArc, setSelectedArc] = useState<NarrativeArc | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('day');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [minSignificance, setMinSignificance] = useState<number>(0);
  const [currentDate, setCurrentDate] = useState<string>('');
  const eventContainerRef = useRef<HTMLDivElement>(null);
  const [tagStats, setTagStats] = useState<Record<string, number>>({});

  // Fetch narrative data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch narrative events
        const eventsResponse = await fetch('http://localhost:8000/simulations/current/narrative/events?limit=100');
        if (eventsResponse.ok) {
          const eventsData = await eventsResponse.json();
          setEvents(eventsData);
          
          // Calculate tag statistics
          const tags: Record<string, number> = {};
          eventsData.forEach((event: NarrativeEvent) => {
            event.tags.forEach(tag => {
              tags[tag] = (tags[tag] || 0) + 1;
            });
          });
          setTagStats(tags);
        }
        
        // Fetch narrative summary
        const summaryResponse = await fetch(`http://localhost:8000/simulations/current/narrative/summary?period=${selectedPeriod}`);
        if (summaryResponse.ok) {
          const summaryData = await summaryResponse.json();
          setNarrativeSummary(summaryData.summary);
          setCurrentDate(summaryData.date);
        }
        
        // Fetch some agents for reference
        const agentsResponse = await fetch('http://localhost:8000/simulations/current/agents?limit=200');
        if (agentsResponse.ok) {
          const agentsData = await agentsResponse.json();
          const agentsMap: Record<string, Agent> = {};
          agentsData.forEach((agent: Agent) => {
            agentsMap[agent.id] = agent;
          });
          setAgents(agentsMap);
        }
        
        // For MVP: Generate sample narrative arcs
        // In a full implementation, this would be fetched from API
        generateSampleArcs();
        
      } catch (error) {
        console.error('Error fetching narrative data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [selectedPeriod]);

  // Generate sample narrative arcs for the MVP
  const generateSampleArcs = () => {
    const sampleArcs: NarrativeArc[] = [
      {
        id: 'arc1',
        title: 'Rising Tensions in Olympus City',
        description: 'A series of economic disputes between Terra Corp representatives and Mars Natives is creating a powder keg situation in Olympus City.',
        agents_involved: ['agent1', 'agent2', 'agent3'],
        start_time: new Date(Date.now() - 86400000 * 3).toISOString(),
        is_complete: false,
        events: []
      },
      {
        id: 'arc2',
        title: 'Underground Network Expansion',
        description: 'The underground faction is rapidly expanding its influence through a sophisticated network of black market trades.',
        agents_involved: ['agent4', 'agent5'],
        start_time: new Date(Date.now() - 86400000 * 5).toISOString(),
        is_complete: false,
        events: []
      },
      {
        id: 'arc3',
        title: 'Resource Crisis in Valles Marineris',
        description: 'Dwindling oxygen supplies in Valles Marineris have led to increasing prices and social unrest.',
        agents_involved: ['agent6', 'agent7', 'agent8'],
        start_time: new Date(Date.now() - 86400000 * 2).toISOString(),
        is_complete: false,
        events: []
      }
    ];
    
    setNarrativeArcs(sampleArcs);
  };

  // Apply filters when events or filter settings change
  useEffect(() => {
    let filtered = [...events];
    
    // Apply tag filter
    if (selectedTags.length > 0) {
      filtered = filtered.filter(event => 
        selectedTags.some(tag => event.tags.includes(tag))
      );
    }
    
    // Apply significance filter
    if (minSignificance > 0) {
      filtered = filtered.filter(event => event.significance >= minSignificance);
    }
    
    // Sort by timestamp (most recent first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    setFilteredEvents(filtered);
    
    // Select first event if none selected
    if (!selectedEvent && filtered.length > 0) {
      setSelectedEvent(filtered[0]);
    }
  }, [events, selectedTags, minSignificance]);

  // Handle event selection
  const handleEventClick = (event: NarrativeEvent) => {
    setSelectedEvent(event);
    setSelectedArc(null);
    
    // Scroll to top on mobile
    if (window.innerWidth < 768) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Handle arc selection
  const handleArcClick = (arc: NarrativeArc) => {
    setSelectedArc(arc);
    setSelectedEvent(null);
    
    // Scroll to top on mobile
    if (window.innerWidth < 768) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Toggle tag selection
  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  // Format date helper
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Get agent name helper
  const getAgentName = (agentId: string) => {
    return agents[agentId]?.name || 'Unknown Agent';
  };

  // Get agent faction helper
  const getAgentFaction = (agentId: string) => {
    return agents[agentId]?.faction || 'unknown';
  };

  // Navigate between events
  const navigateEvent = (direction: 'prev' | 'next') => {
    if (!selectedEvent || filteredEvents.length === 0) return;
    
    const currentIndex = filteredEvents.findIndex(e => e.id === selectedEvent.id);
    if (currentIndex === -1) return;
    
    if (direction === 'prev' && currentIndex > 0) {
      setSelectedEvent(filteredEvents[currentIndex - 1]);
    } else if (direction === 'next' && currentIndex < filteredEvents.length - 1) {
      setSelectedEvent(filteredEvents[currentIndex + 1]);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw size={24} className="animate-spin text-purple-500" />
          <span>Loading narrative data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <Head>
        <title>Narrative Chronicle | ProtoNomia</title>
      </Head>

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 text-transparent bg-clip-text">
                Narrative Chronicle
              </h1>
              <p className="text-gray-400">
                The unfolding story of Mars in 2993
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

        {/* Summary */}
        <div className="bg-gray-900 rounded-lg p-6 shadow-lg mb-8">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <BookOpen size={18} className="mr-2 text-cyan-400" />
              Narrative Summary
            </h2>
            
            <div className="flex items-center space-x-2">
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="bg-gray-800 text-white px-3 py-1 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-purple-500"
              >
                <option value="day">Daily</option>
                <option value="week">Weekly</option>
                <option value="month">Monthly</option>
              </select>
              
              <div className="text-sm text-gray-400 flex items-center">
                <Calendar size={14} className="mr-1" />
                <span>{formatDate(currentDate).split(',')[0]}</span>
              </div>
            </div>
          </div>
          
          <div className="prose prose-invert prose-sm max-w-none">
            <p className="text-gray-300 leading-relaxed">{narrativeSummary}</p>
          </div>
        </div>

        {/* Main content - narrative events and details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar / Filters */}
          <div className="lg:col-span-1 space-y-6">
            {/* Filters */}
            <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
              <h2 className="text-lg font-semibold mb-4 flex items-center">
                <Filter size={16} className="mr-2" />
                <span>Filters</span>
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Minimum Significance</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={minSignificance}
                    onChange={(e) => setMinSignificance(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Any</span>
                    <span>{minSignificance.toFixed(1)}</span>
                    <span>Critical</span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-gray-400 text-sm mb-2 flex items-center">
                    <Tag size={14} className="mr-1" />
                    <span>Tags</span>
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(tagStats)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 10)
                      .map(([tag, count]) => (
                        <button
                          key={tag}
                          onClick={() => toggleTag(tag)}
                          className={`text-xs px-2 py-1 rounded-full ${
                            selectedTags.includes(tag)
                              ? 'bg-purple-600 text-white'
                              : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                          }`}
                        >
                          {tag} ({count})
                        </button>
                      ))}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Active Arcs */}
            <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
              <h2 className="text-lg font-semibold mb-4 flex items-center">
                <BookMarked size={16} className="mr-2 text-purple-400" />
                <span>Narrative Arcs</span>
              </h2>
              
              {narrativeArcs.length > 0 ? (
                <div className="space-y-4">
                  {narrativeArcs.map((arc) => (
                    <div 
                      key={arc.id}
                      onClick={() => handleArcClick(arc)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors hover:bg-gray-800 ${
                        selectedArc?.id === arc.id ? 'bg-gray-800 border-l-4 border-purple-500' : ''
                      }`}
                    >
                      <h3 className="font-medium text-purple-300">{arc.title}</h3>
                      <p className="text-xs text-gray-400 mt-1">
                        Started {formatDate(arc.start_time).split(',')[0]}
                      </p>
                      <div className="flex items-center mt-2 text-xs text-gray-500">
                        <Users size={12} className="mr-1" />
                        <span>{arc.agents_involved.length} agents involved</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-gray-500 py-4 text-center">
                  No active narrative arcs
                </div>
              )}
            </div>
          </div>
          
          {/* Events List */}
          <div className="bg-gray-900 rounded-lg shadow-lg overflow-hidden">
            <div className="p-4 border-b border-gray-800 flex justify-between items-center">
              <h2 className="text-lg font-semibold">Events</h2>
              <span className="text-sm text-gray-400">{filteredEvents.length} events</span>
            </div>
            
            <div className="overflow-y-auto" style={{ maxHeight: '600px' }} ref={eventContainerRef}>
              {filteredEvents.length > 0 ? (
                <div className="divide-y divide-gray-800">
                  {filteredEvents.map((event) => (
                    <div 
                      key={event.id}
                      onClick={() => handleEventClick(event)}
                      className={`p-4 cursor-pointer transition-colors hover:bg-gray-800 ${
                        selectedEvent?.id === event.id ? 'bg-gray-800 border-l-4 border-purple-500' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium text-white">{event.title}</h3>
                        <div className="flex items-center text-xs text-gray-400">
                          <Star size={14} className="mr-1" />
                          <span>{event.significance.toFixed(1)}</span>
                        </div>
                      </div>
                      
                      <p className="text-sm text-gray-300 line-clamp-2 mb-2">
                        {event.description}
                      </p>
                      
                      <div className="flex justify-between items-center mt-2">
                        <div className="flex space-x-1 text-xs">
                          {event.tags.slice(0, 3).map((tag) => (
                            <span key={tag} className="px-2 py-0.5 bg-gray-800 rounded-full">
                              {tag}
                            </span>
                          ))}
                          {event.tags.length > 3 && (
                            <span className="px-2 py-0.5 bg-gray-800 rounded-full">
                              +{event.tags.length - 3}
                            </span>
                          )}
                        </div>
                        
                        <div className="text-xs text-gray-500 flex items-center">
                          <Clock size={12} className="mr-1" />
                          <span>{formatDate(event.timestamp).split(', ')[1]}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-gray-500">
                  No events match your filters
                </div>
              )}
            </div>
          </div>
          
          {/* Event Details */}
          <div className="bg-gray-900 rounded-lg shadow-lg p-6">
            {selectedEvent ? (
              <div>
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-xl font-semibold text-white">
                    {selectedEvent.title}
                  </h2>
                  
                  <div className="flex items-center space-x-1 px-2 py-1 bg-gray-800 rounded-md text-xs">
                    <Star size={14} className="text-yellow-400" />
                    <span className="text-gray-300">Significance: {selectedEvent.significance.toFixed(1)}</span>
                  </div>
                </div>
                
                <div className="flex items-center text-sm text-gray-400 mb-4">
                  <Calendar size={14} className="mr-1" />
                  <span>{formatDate(selectedEvent.timestamp)}</span>
                </div>
                
                <div className="prose prose-invert prose-sm max-w-none mb-6">
                  <p className="text-gray-300 leading-relaxed">{selectedEvent.description}</p>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-md font-semibold mb-2 flex items-center">
                    <Users size={14} className="mr-2 text-blue-400" />
                    <span>Agents Involved</span>
                  </h3>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {selectedEvent.agents_involved.map((agentId) => (
                      <div key={agentId} className="flex items-center p-2 bg-gray-800 rounded-md">
                        <div className={`w-2 h-2 rounded-full mr-2 ${
                          getAgentFaction(agentId) === 'terra_corporation' ? 'bg-blue-500' :
                          getAgentFaction(agentId) === 'mars_native' ? 'bg-red-500' :
                          getAgentFaction(agentId) === 'independent' ? 'bg-yellow-500' :
                          getAgentFaction(agentId) === 'government' ? 'bg-green-500' :
                          'bg-purple-500'
                        }`} />
                        <span className="text-sm">{getAgentName(agentId)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-md font-semibold mb-2 flex items-center">
                    <Tag size={14} className="mr-2 text-purple-400" />
                    <span>Tags</span>
                  </h3>
                  
                  <div className="flex flex-wrap gap-2">
                    {selectedEvent.tags.map((tag) => (
                      <span key={tag} className="px-2 py-1 bg-gray-800 rounded-md text-xs">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="flex justify-between mt-6 pt-4 border-t border-gray-800">
                  <button 
                    onClick={() => navigateEvent('prev')}
                    className="flex items-center text-sm text-gray-400 hover:text-white"
                    disabled={filteredEvents.indexOf(selectedEvent) === 0}
                  >
                    <ArrowLeft size={16} className="mr-1" />
                    <span>Previous</span>
                  </button>
                  
                  <button 
                    onClick={() => navigateEvent('next')}
                    className="flex items-center text-sm text-gray-400 hover:text-white"
                    disabled={filteredEvents.indexOf(selectedEvent) === filteredEvents.length - 1}
                  >
                    <span>Next</span>
                    <ArrowRight size={16} className="ml-1" />
                  </button>
                </div>
              </div>
            ) : selectedArc ? (
              <div>
                <div className="mb-4">
                  <h2 className="text-xl font-semibold text-white">
                    {selectedArc.title}
                  </h2>
                  <div className="flex items-center text-sm text-gray-400 mt-1">
                    <Calendar size={14} className="mr-1" />
                    <span>Started {formatDate(selectedArc.start_time)}</span>
                    {selectedArc.is_complete && selectedArc.end_time && (
                      <>
                        <span className="mx-2">•</span>
                        <span>Ended {formatDate(selectedArc.end_time)}</span>
                      </>
                    )}
                  </div>
                </div>
                
                <div className="prose prose-invert prose-sm max-w-none mb-6">
                  <p className="text-gray-300 leading-relaxed">{selectedArc.description}</p>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-md font-semibold mb-2 flex items-center">
                    <Users size={14} className="mr-2 text-blue-400" />
                    <span>Key Agents</span>
                  </h3>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {selectedArc.agents_involved.map((agentId) => (
                      <div key={agentId} className="flex items-center p-2 bg-gray-800 rounded-md">
                        <div className={`w-2 h-2 rounded-full mr-2 ${
                          getAgentFaction(agentId) === 'terra_corporation' ? 'bg-blue-500' :
                          getAgentFaction(agentId) === 'mars_native' ? 'bg-red-500' :
                          getAgentFaction(agentId) === 'independent' ? 'bg-yellow-500' :
                          getAgentFaction(agentId) === 'government' ? 'bg-green-500' :
                          'bg-purple-500'
                        }`} />
                        <span className="text-sm">{getAgentName(agentId)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-md font-semibold mb-4 flex items-center">
                    <MessageSquare size={14} className="mr-2 text-green-400" />
                    <span>Arc Progress</span>
                  </h3>
                  
                  <div className="relative pl-4 border-l-2 border-purple-600 space-y-6">
                    {/* For MVP we'll show placeholder events */}
                    <div>
                      <div className="absolute -left-1.5 mt-1.5 w-3 h-3 bg-purple-600 rounded-full"></div>
                      <h4 className="text-white font-medium">Arc Beginning</h4>
                      <p className="text-sm text-gray-300 mt-1">
                        Tensions began to rise when resources were distributed unequally among factions.
                      </p>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(selectedArc.start_time)}
                      </div>
                    </div>
                    
                    <div>
                      <div className="absolute -left-1.5 mt-1.5 w-3 h-3 bg-purple-600 rounded-full"></div>
                      <h4 className="text-white font-medium">Key Development</h4>
                      <p className="text-sm text-gray-300 mt-1">
                        The situation escalated when trade negotiations broke down between major factions.
                      </p>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(new Date(new Date(selectedArc.start_time).getTime() + 86400000).toISOString())}
                      </div>
                    </div>
                    
                    <div>
                      <div className="absolute -left-1.5 mt-1.5 w-3 h-3 bg-purple-600 rounded-full"></div>
                      <h4 className="text-white font-medium">Current Status</h4>
                      <p className="text-sm text-gray-300 mt-1">
                        Multiple agents are now involved in complex negotiation and alliance-forming.
                      </p>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(new Date().toISOString())}
                      </div>
                    </div>
                    
                    {!selectedArc.is_complete && (
                      <div>
                        <div className="absolute -left-1.5 mt-1.5 w-3 h-3 border-2 border-gray-600 rounded-full"></div>
                        <h4 className="text-gray-400 font-medium">Resolution</h4>
                        <p className="text-sm text-gray-500 mt-1">
                          This narrative arc is still developing...
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center text-gray-500 py-12">
                  <FileText size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Select an event or arc to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NarrativePage;