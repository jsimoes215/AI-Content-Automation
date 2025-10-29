import { useState, useEffect } from 'react';
import { Search, Filter, Tag, Clock, Star } from 'lucide-react';
import apiClient from '../lib/api';

interface LibraryItem {
  id: string;
  scene_id: string;
  voiceover_text: string;
  visual_description: string;
  duration: number;
  specific_tags: string[];
  generic_tags: string[];
  usage_count: number;
  performance_score: number;
  library_category: string;
}

export default function ContentLibrary() {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTags, setSearchTags] = useState('');
  const [filterCategory, setFilterCategory] = useState('');

  useEffect(() => {
    loadLibrary();
  }, []);

  const loadLibrary = async () => {
    try {
      setLoading(true);
      const tags = searchTags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      const response = await apiClient.searchLibrary({
        tags: tags.length > 0 ? tags : undefined,
        limit: 50,
      });
      setItems(response.data);
    } catch (error) {
      console.error('Failed to load library:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadLibrary();
  };

  const filteredItems = filterCategory
    ? items.filter((item) => item.library_category === filterCategory)
    : items;

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      high_performance: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      experimental: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      archived: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      favorite: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    };
    return colors[category] || colors.experimental;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Content Library
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Browse and reuse your best scenes
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Tag className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by tags (comma-separated)..."
              value={searchTags}
              onChange={(e) => setSearchTags(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            <option value="high_performance">High Performance</option>
            <option value="experimental">Experimental</option>
            <option value="favorite">Favorite</option>
            <option value="archived">Archived</option>
          </select>
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all"
          >
            <Search className="w-5 h-5 inline mr-2" />
            Search
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredItems.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-4">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(
                    item.library_category
                  )}`}
                >
                  {item.library_category.replace('_', ' ')}
                </span>
                <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{item.duration}s</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-yellow-500" />
                    <span>{item.performance_score.toFixed(1)}</span>
                  </div>
                </div>
              </div>

              <p className="text-gray-900 dark:text-white font-medium mb-2">
                {item.voiceover_text.substring(0, 100)}
                {item.voiceover_text.length > 100 ? '...' : ''}
              </p>

              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {item.visual_description.substring(0, 120)}
                {item.visual_description.length > 120 ? '...' : ''}
              </p>

              <div className="space-y-2">
                {item.specific_tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {item.specific_tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 text-xs rounded-md"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                {item.generic_tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {item.generic_tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400 text-xs rounded-md"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800 flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                <span>Used {item.usage_count} times</span>
                <button className="text-blue-600 dark:text-blue-400 hover:underline">
                  Use in Project
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
          <p className="text-gray-600 dark:text-gray-400">No content found</p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            Try adjusting your search criteria
          </p>
        </div>
      )}
    </div>
  );
}
