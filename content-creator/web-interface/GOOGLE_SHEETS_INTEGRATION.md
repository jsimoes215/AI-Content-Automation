# Google Sheets Integration Documentation

This document provides comprehensive information about the Google Sheets integration for the AI Content Automation System.

## Overview

The Google Sheets integration allows users to connect their Google Sheets to the AI content automation system, enabling:

- **Data Import**: Import content data from Google Sheets
- **Data Export**: Export generated content back to Google Sheets  
- **Real-time Sync**: Keep data synchronized between the system and sheets
- **Bulk Processing**: Process multiple content items from a single sheet
- **Content Automation**: Automated content generation based on sheet data

## Architecture

### Frontend Components

1. **GoogleSheetsConnection.tsx** - Main connection management page
2. **googleSheetsClient.ts** - Client-side Google Sheets API wrapper
3. **api.ts** - Backend API client methods

### Backend Integration

The frontend communicates with backend endpoints:

```
/api/google-sheets/auth-url          - Get OAuth URL for authentication
/api/google-sheets/auth-status       - Check authentication status
/api/google-sheets/spreadsheets      - List user's spreadsheets
/api/google-sheets/connections       - List/create/delete connections
/api/google-sheets/connections/:id   - Get/update specific connection
/api/google-sheets/connections/:id/test - Test connection
/api/google-sheets/connections/:id/data - Read/write sheet data
```

## Features

### 1. Authentication Flow

- OAuth 2.0 integration with Google
- Secure token management
- Authentication status tracking
- Multi-account support

### 2. Connection Management

- Create named connections to specific spreadsheets
- Configure read/write permissions
- Test connection functionality
- Delete unwanted connections

### 3. Sheet Configuration

- Select specific worksheets
- Define data ranges
- Configure column mappings
- Set up automation triggers

### 4. Data Operations

- Read data from sheets
- Write data to sheets
- Append new rows
- Clear ranges
- Batch operations

## Usage

### Setting Up Google Sheets Integration

1. **Navigate to Google Sheets Page**
   ```
   /google-sheets
   ```

2. **Authenticate with Google**
   - Click "Connect Google Sheets"
   - Complete OAuth flow
   - Grant necessary permissions

3. **Create a Connection**
   - Select spreadsheet from your Google Drive
   - Choose specific worksheet
   - Define data range
   - Set connection name
   - Configure permissions

### API Usage Examples

```typescript
import apiClient from '../lib/api';

// List existing connections
const connections = await apiClient.listGoogleSheetsConnections();

// Create new connection
const newConnection = await apiClient.createGoogleSheetsConnection({
  spreadsheet_id: '1abc123...',
  spreadsheet_name: 'My Content Data',
  name: 'Content Input',
  sheet_name: 'Sheet1',
  range: 'A:Z',
  permissions: 'read'
});

// Read data from sheet
const data = await apiClient.getGoogleSheetsData('connection-id', 'Sheet1');

// Write data to sheet
await apiClient.writeToGoogleSheets('connection-id', [
  ['Title', 'Content', 'Status'],
  ['Video 1', 'Generated content...', 'Completed']
], 'Sheet1');
```

### Client-Side Google Sheets API

```typescript
import { googleSheetsClient, DEFAULT_GOOGLE_SHEETS_CONFIG } from '../lib/googleSheetsClient';

// Initialize
await googleSheetsClient.init({
  apiKey: 'your-api-key',
  discoveryDocs: DEFAULT_GOOGLE_SHEETS_CONFIG.discoveryDocs
});

// Sign in
await googleSheetsClient.signIn(['https://www.googleapis.com/auth/spreadsheets']);

// Read sheet data
const sheetData = await googleSheetsClient.readSheet('spreadsheet-id', 'A1:E100');

// Write data
await googleSheetsClient.writeSheet('spreadsheet-id', 'A1:E1', [
  ['Name', 'Email', 'Status']
]);
```

## Data Formats

### Spreadsheet Structure

Recommended column structure for content automation:

| Column | Purpose | Example |
|--------|---------|---------|
| A | Title/Name | "How to Start a Blog" |
| B | Content/Description | "Complete guide for beginners..." |
| C | Target Audience | "blogging beginners" |
| D | Tone | "educational" |
| E | Status | "draft" |
| F | Platform | "YouTube" |
| G | Duration (min) | "5" |
| H | Generated At | "2024-01-15 10:30" |

### JSON Data Format

```json
{
  "connection_id": "conn_123",
  "spreadsheet_id": "1abc...",
  "sheet_name": "Content Ideas",
  "range": "A:H",
  "data": [
    {
      "title": "Video Title",
      "content": "Description...",
      "audience": "target audience",
      "tone": "professional",
      "status": "draft"
    }
  ]
}
```

## Security Considerations

### Permissions

- **Read Only**: View and extract data from sheets
- **Write**: Modify existing data and add new content
- **Admin**: Full control including sheet creation/deletion

### Data Privacy

- OAuth tokens are securely stored
- No sensitive data is logged
- User data remains in their Google account
- All API calls use HTTPS

### Best Practices

1. **Least Privilege**: Request only necessary permissions
2. **Token Management**: Implement proper token refresh handling
3. **Data Validation**: Validate all input data before processing
4. **Error Handling**: Gracefully handle API errors and rate limits
5. **Rate Limiting**: Respect Google Sheets API rate limits

## Error Handling

### Common Error Scenarios

1. **Authentication Failed**
   - Check OAuth configuration
   - Verify redirect URIs
   - Ensure proper scopes

2. **Permission Denied**
   - User may not have access to spreadsheet
   - Check sheet sharing settings
   - Verify connection permissions

3. **Rate Limit Exceeded**
   - Implement exponential backoff
   - Cache frequently accessed data
   - Use batch operations when possible

4. **Invalid Range**
   - Verify sheet name and cell range
   - Check for typos in A1 notation
   - Ensure range exists and is accessible

## Integration Examples

### Bulk Content Generation

```typescript
// Read content ideas from sheet
const contentData = await apiClient.getGoogleSheetsData(connectionId, 'Content Ideas');

// Process each row
for (const row of contentData.values) {
  const [title, description, audience, tone] = row;
  
  // Generate content
  const generatedContent = await generateContent({
    title,
    description,
    audience,
    tone
  });
  
  // Update status in sheet
  await apiClient.writeToGoogleSheets(connectionId, [
    [title, description, audience, tone, 'generated', generatedContent]
  ], 'Content Ideas');
}
```

### Real-time Data Sync

```typescript
// Connect WebSocket for real-time updates
apiClient.connectWebSocket((data) => {
  if (data.type === 'sheet_update') {
    // Refresh connection data
    loadConnections();
  }
});
```

## Testing

### Manual Testing

1. Create test spreadsheet
2. Add sample data
3. Test authentication flow
4. Verify all CRUD operations
5. Test error scenarios

### Unit Tests

```typescript
import { GoogleSheetsUtils } from '../lib/googleSheetsClient';

describe('GoogleSheetsUtils', () => {
  test('converts array to objects correctly', () => {
    const data = [
      ['Name', 'Age', 'City'],
      ['John', '25', 'NYC'],
      ['Jane', '30', 'LA']
    ];
    
    const result = GoogleSheetsUtils.arrayToObjects(data);
    
    expect(result).toEqual([
      { Name: 'John', Age: '25', City: 'NYC' },
      { Name: 'Jane', Age: '30', City: 'LA' }
    ]);
  });
});
```

## Troubleshooting

### Common Issues

1. **"gapi not loaded"**
   - Ensure Google API script is loaded
   - Check script loading order
   - Verify API key configuration

2. **OAuth redirect URI mismatch**
   - Check registered URIs in Google Console
   - Verify environment-specific URLs
   - Ensure HTTPS in production

3. **CORS issues**
   - Use proper API endpoints
   - Enable CORS in backend
   - Check origin whitelist

4. **Token expired**
   - Implement automatic token refresh
   - Handle 401 responses gracefully
   - Provide re-authentication UI

## Future Enhancements

1. **Advanced Data Validation**
   - Schema validation
   - Data type checking
   - Business rule enforcement

2. **Real-time Collaboration**
   - Multi-user editing
   - Change notifications
   - Conflict resolution

3. **Advanced Analytics**
   - Usage metrics
   - Performance tracking
   - Error reporting

4. **Template Management**
   - Pre-built sheet templates
   - Custom field mapping
   - Workflow automation

## Support

For technical support and questions:
- Check the main application documentation
- Review Google Sheets API documentation
- Contact the development team for integration issues