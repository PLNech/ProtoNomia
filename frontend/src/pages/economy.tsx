import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { 
  Home, 
  TrendingUp, 
  RefreshCw,
  DollarSign,
  BarChart2,
  Scale,
  ArrowDown,
  ArrowUp,
  Briefcase,
  ShoppingBag,
  Zap,
  AlertTriangle,
  Globe,
  Droplet,
  Cpu,
  Package,
  Database,
  Shield
} from 'lucide-react';
import { PieChart, Pie, Cell, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Type definitions
type EconomicReport = {
  indicators: {
    average_wealth: number;
    gini_coefficient: number;
    unemployment_rate: number;
    inflation_rate: number;
    economic_growth: number;
    terra_mars_trade_balance: number;
    public_goods_contribution_rate: number;
    market_stability: number;
    innovation_index: number;
    resource_scarcity: number;
  };
  resource_distribution: Record<string, number>;
  faction_wealth: Record<string, number>;
  active_interactions_by_type: Record<string, number>;
};

type MarketItem = {
  item_type: string;
  avg_price: number;
  availability: number;
  trend: number; // -1, 0, 1
};

type InteractionData = {
  time: string;
  ultimatum_game: number;
  trust_game: number;
  public_goods_game: number;
  oligopoly_collusion: number;
  principal_agent: number;
};

type ResourceTrend = {
  time: string;
  credits: number;
  oxygen: number;
  water: number;
  digital_goods: number;
  physical_goods: number;
};

// Main component
const EconomyPage = () => {
  const [economicReport, setEconomicReport] = useState<EconomicReport | null>(null);
  const [marketItems, setMarketItems] = useState<MarketItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTimePeriod, setSelectedTimePeriod] = useState<string>('day');
  const [interactionData, setInteractionData] = useState<InteractionData[]>([]);
  const [resourceTrends, setResourceTrends] = useState<ResourceTrend[]>([]);
  const [factionWealthData, setFactionWealthData] = useState<any[]>([]);
  
  // Custom colors for charts
  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', '#00C49F'];
  const FACTION_COLORS = {
    'terra_corporation': '#0088FE',
    'mars_native': '#FF6B6B',
    'independent': '#FFD166',
    'government': '#06D6A0',
    'underground': '#9381FF'
  };
  
  // Fetch economic data
  useEffect(() => {
    const fetchEconomicData = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('http://localhost:8000/simulations/current/economy');
        if (response.ok) {
          const data = await response.json();
          setEconomicReport(data);
          
          // Process faction wealth data for pie chart
          if (data.faction_wealth) {
            const factionData = Object.entries(data.faction_wealth).map(([faction, wealth]) => ({
              name: faction.replace('_', ' '),
              value: wealth,
              key: faction
            }));
            setFactionWealthData(factionData);
          }
          
          // Generate mock market data for MVP
          generateMockMarketData();
          
          // Generate mock historical data
          generateMockHistoricalData();
        }
      } catch (error) {
        console.error('Error fetching economic data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchEconomicData();
  }, []);
  
  // Generate mock market data for MVP
  const generateMockMarketData = () => {
    const mockItems: MarketItem[] = [
      { 
        item_type: 'Oxygen',
        avg_price: 25.8,
        availability: 0.72,
        trend: 1
      },
      { 
        item_type: 'Water',
        avg_price: 18.4,
        availability: 0.65,
        trend: 0
      },
      { 
        item_type: 'Food',
        avg_price: 42.3,
        availability: 0.81,
        trend: 0
      },
      { 
        item_type: 'Housing',
        avg_price: 350.6,
        availability: 0.45,
        trend: -1
      },
      { 
        item_type: 'Digital Entertainment',
        avg_price: 15.9,
        availability: 0.95,
        trend: 1
      },
      { 
        item_type: 'Technical Software',
        avg_price: 120.5,
        availability: 0.88,
        trend: 1
      },
      { 
        item_type: 'Minerals',
        avg_price: 68.2,
        availability: 0.54,
        trend: -1
      },
      { 
        item_type: 'Energy Units',
        avg_price: 39.7,
        availability: 0.76,
        trend: 0
      },
      { 
        item_type: 'Medical Supplies',
        avg_price: 87.3,
        availability: 0.62,
        trend: 1
      },
      { 
        item_type: 'Security Services',
        avg_price: 112.8,
        availability: 0.7,
        trend: 0
      }
    ];
    
    setMarketItems(mockItems);
  };
  
  // Generate mock historical data for MVP
  const generateMockHistoricalData = () => {
    // Interactions data
    const mockInteractionData: InteractionData[] = [];
    const now = new Date();
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      mockInteractionData.push({
        time: date.toISOString().split('T')[0],
        ultimatum_game: Math.floor(Math.random() * 15) + 5,
        trust_game: Math.floor(Math.random() * 12) + 3,
        public_goods_game: Math.floor(Math.random() * 8) + 2,
        oligopoly_collusion: Math.floor(Math.random() * 5) + 1,
        principal_agent: Math.floor(Math.random() * 7) + 2
      });
    }
    
    setInteractionData(mockInteractionData);
    
    // Resource trends
    const mockResourceTrends: ResourceTrend[] = [];
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      mockResourceTrends.push({
        time: date.toISOString().split('T')[0],
        credits: 1000 + Math.floor(Math.random() * 200) + (30 - i) * 15,
        oxygen: 100 - i * 0.5 + Math.floor(Math.random() * 10),
        water: 80 - i * 0.3 + Math.floor(Math.random() * 8),
        digital_goods: 200 + Math.floor(Math.random() * 40) + (30 - i) * 5,
        physical_goods: 150 + Math.floor(Math.random() * 30) + (30 - i) * 3
      });
    }
    
    setResourceTrends(mockResourceTrends);
  };
  
  // Format number with sign
  const formatWithSign = (value: number): string => {
    return value > 0 ? `+${value.toFixed(1)}%` : `${value.toFixed(1)}%`;
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw size={24} className="animate-spin text-purple-500" />
          <span>Loading economic data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <Head>
        <title>Economy | ProtoNomia</title>
      </Head>

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 text-transparent bg-clip-text">
                Mars Economy
              </h1>
              <p className="text-gray-400">
                Economic data and market analysis
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={selectedTimePeriod}
                onChange={(e) => setSelectedTimePeriod(e.target.value)}
                className="bg-gray-800 text-white px-3 py-2 rounded-md focus:outline-none focus:ring-1 focus:ring-purple-500"
              >
                <option value="day">Last 24 Hours</option>
                <option value="week">Last Week</option>
                <option value="month">Last Month</option>
              </select>
              
              <Link href="/dashboard" className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-md flex items-center space-x-2">
                <Home size={16} />
                <span>Dashboard</span>
              </Link>
            </div>
          </div>
        </header>

        {/* Economic Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-300 flex items-center">
                <DollarSign size={16} className="mr-1 text-green-400" />
                Average Wealth
              </h3>
              <div className={`text-xs px-2 py-0.5 rounded-full ${
                (economicReport?.indicators.economic_growth || 0) > 0
                  ? 'bg-green-900 text-green-300'
                  : 'bg-red-900 text-red-300'
              }`}>
                {formatWithSign(economicReport?.indicators.economic_growth ?? 0 * 100)}
              </div>
            </div>
            <div className="text-2xl font-bold mb-1">
              {economicReport?.indicators.average_wealth.toFixed(0) || 0} credits
            </div>
            <div className="text-sm text-gray-500">
              per capita
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-300 flex items-center">
                <Scale size={16} className="mr-1 text-blue-400" />
                Inequality Index
              </h3>
            </div>
            <div className="text-2xl font-bold mb-1">
              {economicReport?.indicators.gini_coefficient.toFixed(2) || 0}
            </div>
            <div className="text-sm text-gray-500">
              Gini coefficient
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-300 flex items-center">
                <BarChart2 size={16} className="mr-1 text-purple-400" />
                Market Stability
              </h3>
            </div>
            <div className="text-2xl font-bold mb-1">
              {((economicReport?.indicators.market_stability ?? 0) * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-500">
              economic confidence
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-300 flex items-center">
                <Globe size={16} className="mr-1 text-cyan-400" />
                Terra-Mars Trade
              </h3>
              <div className={`text-xs px-2 py-0.5 rounded-full ${
                (economicReport?.indicators.terra_mars_trade_balance || 0) > 0
                  ? 'bg-green-900 text-green-300'
                  : 'bg-red-900 text-red-300'
              }`}>
                {formatWithSign(economicReport?.indicators.terra_mars_trade_balance ?? 0 * 100)}
              </div>
            </div>
            <div className="text-2xl font-bold mb-1">
              {((economicReport?.indicators.terra_mars_trade_balance ?? 0) * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-500">
              trade balance
            </div>
          </div>
        </div>

        {/* Resource Trends and Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Faction Wealth Distribution */}
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg">
            <h2 className="text-xl font-semibold mb-4">Faction Wealth Distribution</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={factionWealthData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    fill="#8884d8"
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    labelLine={false}
                  >
                    {factionWealthData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={FACTION_COLORS[entry.key as keyof typeof FACTION_COLORS] || COLORS[index % COLORS.length]} 
                      />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value} credits`, 'Wealth']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Total Economy Size</h3>
              <div className="text-2xl font-bold">
                {Object.values(economicReport?.faction_wealth || {}).reduce((a, b) => a + b, 0).toLocaleString()} credits
              </div>
            </div>
          </div>
          
          {/* Resource Trends */}
          <div className="bg-gray-900 rounded-lg p-5 shadow-lg lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Resource Trends</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={resourceTrends.slice(-14)} // Show last 14 days
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis 
                    dataKey="time" 
                    stroke="#888" 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  />
                  <YAxis stroke="#888" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#222', borderColor: '#555' }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(value) => [value, '']}
                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="credits" name="Credits (avg)" stroke="#FFD166" dot={false} />
                  <Line type="monotone" dataKey="oxygen" name="Oxygen" stroke="#06D6A0" dot={false} />
                  <Line type="monotone" dataKey="water" name="Water" stroke="#118AB2" dot={false} />
                  <Line type="monotone" dataKey="digital_goods" name="Digital Goods" stroke="#9381FF" dot={false} />
                  <Line type="monotone" dataKey="physical_goods" name="Physical Goods" stroke="#FF6B6B" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Market and Interactions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Market Prices */}
          <div className="bg-gray-900 rounded-lg shadow-lg lg:col-span-2">
            <div className="p-5 border-b border-gray-800">
              <h2 className="text-xl font-semibold flex items-center">
                <ShoppingBag size={18} className="mr-2 text-purple-400" />
                Mars Market Data
              </h2>
            </div>
            
            <div className="p-4">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-800">
                  <thead>
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Item</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Price (credits)</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Availability</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Trend</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {marketItems.map((item, index) => (
                      <tr key={index} className="hover:bg-gray-800">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center">
                            {item.item_type === 'Oxygen' ? <Droplet size={16} className="mr-2 text-blue-400" /> :
                             item.item_type === 'Water' ? <Droplet size={16} className="mr-2 text-cyan-400" /> :
                             item.item_type === 'Food' ? <ShoppingBag size={16} className="mr-2 text-green-400" /> :
                             item.item_type === 'Digital Entertainment' ? <Cpu size={16} className="mr-2 text-purple-400" /> :
                             item.item_type === 'Technical Software' ? <Cpu size={16} className="mr-2 text-indigo-400" /> :
                             item.item_type === 'Housing' ? <Home size={16} className="mr-2 text-orange-400" /> :
                             item.item_type === 'Minerals' ? <Database size={16} className="mr-2 text-yellow-400" /> :
                             item.item_type === 'Energy Units' ? <Zap size={16} className="mr-2 text-yellow-400" /> :
                             item.item_type === 'Medical Supplies' ? <Package size={16} className="mr-2 text-red-400" /> :
                             item.item_type === 'Security Services' ? <Shield size={16} className="mr-2 text-gray-400" /> :
                             <Package size={16} className="mr-2 text-gray-400" />}
                            {item.item_type}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {item.avg_price.toFixed(1)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="w-24 bg-gray-700 h-2 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${
                                item.availability > 0.7 ? 'bg-green-500' :
                                item.availability > 0.3 ? 'bg-yellow-500' :
                                'bg-red-500'
                              }`}
                              style={{ width: `${item.availability * 100}%` }}
                            />
                          </div>
                          <div className="text-xs text-gray-400 mt-1">
                            {(item.availability * 100).toFixed(0)}%
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {item.trend === 1 ? (
                            <div className="flex items-center text-green-400">
                              <ArrowUp size={14} />
                              <span className="ml-1">Rising</span>
                            </div>
                          ) : item.trend === -1 ? (
                            <div className="flex items-center text-red-400">
                              <ArrowDown size={14} />
                              <span className="ml-1">Falling</span>
                            </div>
                          ) : (
                            <div className="flex items-center text-gray-400">
                              <span>Stable</span>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Resource Scarcity Warning */}
              {(economicReport?.indicators.resource_scarcity || 0) > 0.7 && (
                <div className="mt-4 p-3 bg-red-900/50 border border-red-700 rounded-md flex items-start">
                  <AlertTriangle size={20} className="text-red-400 mr-2 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-medium text-red-300">Resource Scarcity Warning</h3>
                    <p className="text-sm text-red-200 mt-1">
                      Critical resources are becoming scarce. Prices may become unstable and conflicts over resources could increase.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Economic Interactions */}
          <div className="bg-gray-900 rounded-lg shadow-lg">
            <div className="p-5 border-b border-gray-800">
              <h2 className="text-xl font-semibold flex items-center">
                <Briefcase size={18} className="mr-2 text-blue-400" />
                Economic Interactions
              </h2>
            </div>
            
            <div className="p-4">
              <div className="h-64 mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={interactionData.slice(-7)} // Last 7 days
                    margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis 
                      dataKey="time" 
                      stroke="#888" 
                      tick={{ fontSize: 10 }}
                      tickFormatter={(value) => new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                    />
                    <YAxis stroke="#888" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#222', borderColor: '#555' }}
                      labelStyle={{ color: '#fff' }}
                      formatter={(value) => [value, 'interactions']}
                      labelFormatter={(label) => new Date(label).toLocaleDateString()}
                    />
                    <Legend />
                    <Bar dataKey="ultimatum_game" name="Ultimatum" stackId="a" fill="#8884d8" />
                    <Bar dataKey="trust_game" name="Trust" stackId="a" fill="#82ca9d" />
                    <Bar dataKey="public_goods_game" name="Public Goods" stackId="a" fill="#ffc658" />
                    <Bar dataKey="oligopoly_collusion" name="Oligopoly" stackId="a" fill="#ff8042" />
                    <Bar dataKey="principal_agent" name="Principal-Agent" stackId="a" fill="#0088FE" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              
              {/* Active Interactions */}
              <h3 className="text-sm font-medium text-gray-400 mb-2">Active Interaction Types</h3>
              <div className="space-y-2">
                {economicReport && Object.entries(economicReport.active_interactions_by_type)
                  .filter(([_, count]) => count > 0)
                  .sort(([_, countA], [__, countB]) => countB - countA)
                  .slice(0, 5)
                  .map(([type, count]) => (
                    <div key={type} className="flex justify-between items-center">
                      <span className="text-sm capitalize">
                        {type.replace(/_/g, ' ')}
                      </span>
                      <span className="px-2 py-0.5 bg-gray-800 rounded-full text-xs">
                        {count} active
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>

        {/* Navigation footer */}
        <div className="mt-8 pt-6 border-t border-gray-800 flex justify-between">
          <Link href="/dashboard" className="flex items-center text-gray-400 hover:text-white">
            <Home size={18} className="mr-2" />
            <span>Dashboard</span>
          </Link>
          
          <Link href="/agents" className="flex items-center text-gray-400 hover:text-white">
            <Users size={18} className="mr-2" />
            <span>Population</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default EconomyPage;