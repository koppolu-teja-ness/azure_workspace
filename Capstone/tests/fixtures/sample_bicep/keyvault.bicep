// Sample Key Vault Bicep fixture placeholder
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'sample-kv'
  location: resourceGroup().location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
  }
}
