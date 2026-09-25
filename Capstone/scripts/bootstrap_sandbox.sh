#!/usr/bin/env bash
# Phase 0 sandbox bootstrap. Run LOCALLY after `az login` and `aws configure`
# — do not run this in CI, and do not run it against a production account.
set -euo pipefail

AZURE_SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:?set AZURE_SUBSCRIPTION_ID first}"
SP_NAME="migration-assistant-discovery"

echo "== Azure: creating read-only service principal for discovery =="
az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role "Reader" \
  --scopes "/subscriptions/${AZURE_SUBSCRIPTION_ID}"

echo
echo "Copy the appId/password/tenant above into .env as"
echo "  AZURE_CLIENT_ID / AZURE_CLIENT_SECRET / AZURE_TENANT_ID"
echo

AWS_PROFILE_NAME="${AWS_PROFILE:-migration-sandbox}"
POLICY_NAME="migration-assistant-deploy-scoped"

echo "== AWS: drafting a scoped deployment policy (review before use) =="
cat > "/tmp/${POLICY_NAME}.json" <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFormationCore",
      "Effect": "Allow",
      "Action": ["cloudformation:*"],
      "Resource": "*"
    },
    {
      "Sid": "InScopeServices",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:*",
        "kms:*",
        "acm:*",
        "lambda:*",
        "apigateway:*",
        "events:*",
        "s3:GetBucketNotification",
        "s3:PutBucketNotification",
        "sqs:*",
        "ec2:*Vpc*",
        "ec2:*Subnet*",
        "ec2:*SecurityGroup*",
        "ec2:*RouteTable*",
        "ec2:*NetworkAcl*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "iam:GetRole"
      ],
      "Resource": "*"
    }
  ]
}
EOF
echo "Wrote a STARTING POINT policy to /tmp/${POLICY_NAME}.json"
echo "Tighten the Resource ARNs before attaching it to anything but a sandbox."
echo "Create it with:"
echo "  aws iam create-policy --policy-name ${POLICY_NAME} --policy-document file:///tmp/${POLICY_NAME}.json --profile ${AWS_PROFILE_NAME}"
