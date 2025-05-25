name                             = "jark-stack"
enable_aws_efs_csi_driver        = true
enable_jupyterhub                = true
enable_kuberay_operator          = true
enable_argo_workflows            = true
enable_argo_events               = true
enable_argocd                    = true
enable_ai_ml_observability_stack = true

#-----------------------------
# EKS Addons Configuration
#-----------------------------
# The following addons are deployed via the "terraform-aws-modules/eks/aws" module in "eks.tf":
#-----------------------------
# - coredns                        # DNS service for cluster-internal domain name resolution
# - eks-node-monitoring-agent      # Collects node-level metrics and logs
# - eks-pod-identity-agent         # Enables pod IAM roles without IRSA
# - kube-proxy                     # Handles network routing for pods
# - vpc-cni                        # AWS VPC Container Network Interface
# - aws-ebs-csi-driver             # EBS storage provisioning
# - metrics-server                 # Cluster resource metrics collection
# - amazon-cloudwatch-observability # Enhanced monitoring and logging
#-----------------------------
