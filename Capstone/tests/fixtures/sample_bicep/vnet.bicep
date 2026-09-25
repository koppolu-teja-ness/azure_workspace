// Sample VNet Bicep fixture placeholder
resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: 'sample-vnet'
  location: resourceGroup().location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
  }
}
