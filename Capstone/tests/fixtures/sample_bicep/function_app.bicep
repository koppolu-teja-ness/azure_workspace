// Sample Function App Bicep fixture placeholder
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: 'sample-func-app'
  location: resourceGroup().location
  kind: 'functionapp'
  properties: {
    httpsOnly: true
  }
}
