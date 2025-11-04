import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Link as LinkIcon, 
  CheckCircle, 
  AlertCircle, 
  ExternalLink, 
  Download,
  RefreshCw,
  Database,
  FileSpreadsheet,
  Shield,
  Settings
} from 'lucide-react';
import apiClient from '../lib/api';

interface GoogleSheetsConnection {
  id: string;
  name: string;
  spreadsheet_id: string;
  spreadsheet_name: string;
  status: 'connected' | 'disconnected' | 'error';
  permissions: 'read' | 'write' | 'admin';
  last_sync: string;
  created_at: string;
  sheets: Array<{
    id: string;
    name: string;
    range: string;
  }>;
}

interface Spreadsheet {
  id: string;
  name: string;
  owner: string;
  created_time: string;
}

export default function GoogleSheetsConnection() {
  const navigate = useNavigate();
  const [connections, setConnections] = useState<GoogleSheetsConnection[]>([]);
  const [spreadsheets, setSpreadsheets] = useState<Spreadsheet[]>([]);
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [showSheetSelector, setShowSheetSelector] = useState(false);
  const [selectedSpreadsheet, setSelectedSpreadsheet] = useState<Spreadsheet | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>('');
  const [selectedRange, setSelectedRange] = useState<string>('');
  const [connectionName, setConnectionName] = useState('');

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      const response = await apiClient.listGoogleSheetsConnections();
      setConnections(response.data);
    } catch (error) {
      console.error('Failed to load connections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    try {
      setAuthLoading(true);
      // Start OAuth flow
      const response = await apiClient.getGoogleAuthUrl();
      
      // Open Google OAuth in new window
      const authWindow = window.open(
        response.data.auth_url,
        'google-auth',
        'width=500,height=600,scrollbars=yes,resizable=yes'
      );

      // Listen for auth completion
      const authInterval = setInterval(async () => {
        try {
          if (authWindow?.closed) {
            clearInterval(authInterval);
            // Check if auth was successful
            const statusResponse = await apiClient.checkGoogleAuthStatus();
            if (statusResponse.data.connected) {
              await loadSpreadsheets();
              setShowSheetSelector(true);
            }
          }
        } catch (error) {
          clearInterval(authInterval);
          console.error('Auth check failed:', error);
        }
      }, 1000);

    } catch (error) {
      console.error('Auth failed:', error);
      alert('Authentication failed. Please try again.');
    } finally {
      setAuthLoading(false);
    }
  };

  const loadSpreadsheets = async () => {
    try {
      const response = await apiClient.listGoogleSpreadsheets();
      setSpreadsheets(response.data);
    } catch (error) {
      console.error('Failed to load spreadsheets:', error);
    }
  };

  const handleCreateConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSpreadsheet || !selectedSheet) return;

    try {
      const connectionData = {
        spreadsheet_id: selectedSpreadsheet.id,
        spreadsheet_name: selectedSpreadsheet.name,
        name: connectionName || selectedSpreadsheet.name,
        sheet_name: selectedSheet,
        range: selectedRange || 'A:Z',
        permissions: 'read' as const
      };

      await apiClient.createGoogleSheetsConnection(connectionData);
      setShowSheetSelector(false);
      setSelectedSpreadsheet(null);
      setSelectedSheet('');
      setSelectedRange('');
      setConnectionName('');
      loadConnections();
    } catch (error) {
      console.error('Failed to create connection:', error);
      alert('Failed to create connection. Please try again.');
    }
  };

  const handleTestConnection = async (connectionId: string) => {
    try {
      await apiClient.testGoogleSheetsConnection(connectionId);
      loadConnections();
    } catch (error) {
      console.error('Connection test failed:', error);
    }
  };

  const handleDeleteConnection = async (connectionId: string) => {
    if (!confirm('Are you sure you want to delete this connection?')) return;

    try {
      await apiClient.deleteGoogleSheetsConnection(connectionId);
      loadConnections();
    } catch (error) {
      console.error('Failed to delete connection:', error);
      alert('Failed to delete connection.');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'disconnected':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  const getPermissionColor = (permissions: string) => {
    switch (permissions) {
      case 'admin':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400';
      case 'write':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'read':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Google Sheets Connection</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Connect and manage your Google Sheets for content automation
          </p>
        </div>
        <button
          onClick={handleGoogleAuth}
          disabled={authLoading}
          className="flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50"
        >
          {authLoading ? (
            <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
          ) : (
            <LinkIcon className="w-5 h-5 mr-2" />
          )}
          {authLoading ? 'Connecting...' : 'Connect Google Sheets'}
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {connections.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {connections.map((connection) => (
                <div
                  key={connection.id}
                  className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                        <FileSpreadsheet className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {connection.name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {connection.spreadsheet_name}
                        </p>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(connection.status)}`}>
                        {connection.status}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPermissionColor(connection.permissions)}`}>
                        {connection.permissions}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2 mb-4">
                    {connection.sheets.map((sheet) => (
                      <div
                        key={sheet.id}
                        className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {sheet.name}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            Range: {sheet.range}
                          </p>
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-400" />
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-between items-center">
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Last sync: {new Date(connection.last_sync).toLocaleDateString()}
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleTestConnection(connection.id)}
                        className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        title="Test Connection"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteConnection(connection.id)}
                        className="p-2 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                        title="Delete Connection"
                      >
                        <Database className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
              <FileSpreadsheet className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No Google Sheets Connected
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Connect your Google Sheets to start automating your content workflow
              </p>
              <button
                onClick={handleGoogleAuth}
                disabled={authLoading}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50"
              >
                {authLoading ? (
                  <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                ) : (
                  <LinkIcon className="w-5 h-5 mr-2" />
                )}
                {authLoading ? 'Connecting...' : 'Connect Google Sheets'}
              </button>
            </div>
          )}
        </>
      )}

      {showSheetSelector && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-8 max-w-2xl w-full mx-4 shadow-2xl">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              Select Google Sheet
            </h2>

            <form onSubmit={handleCreateConnection} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Connection Name
                </label>
                <input
                  type="text"
                  value={connectionName}
                  onChange={(e) => setConnectionName(e.target.value)}
                  placeholder="My Content Spreadsheet"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Spreadsheet
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-300 dark:border-gray-700 rounded-lg">
                  {spreadsheets.map((sheet) => (
                    <div
                      key={sheet.id}
                      onClick={() => setSelectedSpreadsheet(sheet)}
                      className={`p-3 cursor-pointer transition-colors ${
                        selectedSpreadsheet?.id === sheet.id
                          ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                      }`}
                    >
                      <p className="font-medium text-gray-900 dark:text-white">
                        {sheet.name}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Owner: {sheet.owner}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {selectedSpreadsheet && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Sheet/Worksheet
                    </label>
                    <input
                      type="text"
                      value={selectedSheet}
                      onChange={(e) => setSelectedSheet(e.target.value)}
                      placeholder="Sheet1"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Data Range
                    </label>
                    <input
                      type="text"
                      value={selectedRange}
                      onChange={(e) => setSelectedRange(e.target.value)}
                      placeholder="A:Z (all columns) or A1:E100 (specific range)"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      Example: A:Z for all columns, A1:E100 for specific range
                    </p>
                  </div>
                </>
              )}

              <div className="flex justify-end gap-4">
                <button
                  type="button"
                  onClick={() => setShowSheetSelector(false)}
                  className="px-6 py-2 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedSpreadsheet || !selectedSheet}
                  className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50"
                >
                  Create Connection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}