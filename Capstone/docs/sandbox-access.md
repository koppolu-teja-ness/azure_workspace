# Sandbox Access Validation

## Required identities
- Person A (`koppolu-teja-ness`): Azure read/discovery role + AWS read/lint role
- Person B (`saurav-das-ness`): Azure read role + AWS CloudFormation deploy/validate role

## Identity policy for shared Azure subscription
- Both team members may use the same Azure subscription for sandbox work.
- Do not share Person A credentials with Person B.
- Each person must use their own identity so actions are auditable and access can be revoked safely.
- Grant Person B least-privilege RBAC on the same subscription/resource group used by Person A.

## Temporary fallback if Person B has no Azure account
Use this only until Person B gets separate Azure access.

1. Person A runs Azure-only discovery and export steps.
2. Person A commits generated non-secret artifacts needed by Person B (specs, reports, metadata).
3. Person B continues AWS-side implementation, contract testing, CI, and validation on those artifacts.
4. Track this as an open operational risk and close it once Person B has direct Azure access.

## How to get required IDs

### Azure subscription ID
```powershell
az account show --query id -o tsv
```

### Azure tenant ID
```powershell
az account show --query tenantId -o tsv
```

### AWS account ID
```powershell
aws sts get-caller-identity --query Account --output text
```

### AWS caller ARN (useful for IAM role/user tracing)
```powershell
aws sts get-caller-identity --query Arn --output text
```

## Captured IDs (current validated identity)
- Person A (`koppolu-teja-ness`)
	- Azure subscriptionId: `REDACTED_AZURE_SUBSCRIPTION_ID`
	- Azure tenantId: `REDACTED_AZURE_TENANT_ID`
	- Azure login user: `REDACTED_EMAIL`
	- AWS accountId: `REDACTED_AWS_ACCOUNT_ID`
	- AWS caller ARN: `REDACTED_AWS_CALLER_ARN`

Person B (`saurav-das-ness`) should run the same commands and append their values after Azure access is provisioned.

## Least-privilege baseline
- Azure scope: subscription/resource-group limited `Reader` plus explicit permissions needed for metadata discovery.
- AWS scope: IAM role limited to CloudFormation stack operations, Lambda/VPC/Secrets Manager/KMS read-write in sandbox account only.

## Smoke commands

### Azure
```powershell
az account show
az group list --query "[].name" -o tsv
az resource list --resource-type Microsoft.KeyVault/vaults -o table
```

### AWS
```powershell
aws sts get-caller-identity
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
aws ec2 describe-vpcs --query "Vpcs[].VpcId" --output text
```

## Validation record
| Check | Person A | Person B | Status | Notes |
|---|---|---|---|---|
| Azure login and subscription access | `koppolu-teja-ness` | `saurav-das-ness` | In Progress | Person A captured; Person B pending account provisioning |
| AWS identity and stack listing | `koppolu-teja-ness` | `saurav-das-ness` | In Progress | Person A captured; Person B pending |
| Permission-denied events reviewed | `koppolu-teja-ness` | `saurav-das-ness` | Open | Record denied actions, least-privilege updates, and fallback end date |
