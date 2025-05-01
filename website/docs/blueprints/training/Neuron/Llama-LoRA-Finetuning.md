---
sidebar_label: Llama 3 Fine-tuning with LoRA
---
import CollapsibleContent from '../../../../src/components/CollapsibleContent';

:::warning
To deploy ML models on EKS, you need access to GPUs or Neuron instances. If deployment fails, check if you have access to these resources. If nodes aren't starting, check Karpenter or Node group logs.
:::

:::danger
Note: The Llama 3 model is governed by the Meta license. To download the model weights and tokenizer, visit the [website](https://ai.meta.com/) and accept the license before requesting access.
:::

:::info
We are working to improve this blueprint with better observability, logging, and scalability.
:::

# Llama 3 fine-tuning on Trn1 with HuggingFace Optimum Neuron

This guide shows you how to fine-tune the `Llama3-8B` language model using AWS Trainium (Trn1) EC2 instances. We'll use HuggingFace Optimum Neuron to make integration with Neuron easy.

### What is Llama 3?

Llama 3 is a large language model (LLM) for tasks like text generation, summarization, translation, and question answering. You can fine-tune it for your specific needs.

#### AWS Trainium:
- **Optimized for Deep Learning**: AWS Trainium Trn1 instances are built for deep learning. They offer high throughput and low latency, making them great for training large models like Llama 3.
- **Neuron SDK**: The AWS Neuron SDK helps optimize your models for Trainium. It includes advanced compiler optimizations and supports mixed precision training for faster results without losing accuracy.

## 1. Deploying the Solution

<CollapsibleContent header={<h2><span>Prerequisites</span></h2>}>
Before you start, make sure you have everything you need:
- You can use your local Mac/Windows computer or an Amazon EC2 instance.
- Install Docker (with at least 100GB free space) and make sure your Docker image uses x86 architecture.
- Install these tools and make sure your AWS user or role has the right permissions:
  * [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
  * [kubectl](https://Kubernetes.io/docs/tasks/tools/)
  * [terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
  * Git (only for EC2 instance)
  * Python, pip, jq, unzip

**Clone the ai-on-eks repository:**

Once you have the prerequisites, clone the ai-on-eks GitHub repository:

```bash
git clone https://github.com/awslabs/ai-on-eks.git
```

**Go to the trainium-inferentia directory:**

```bash
cd ai-on-eks/infra/trainium-inferentia
```

In the `terraform` sub-folder, set your preferred AWS region in the `blueprint.tfvars` file.

**Note:** Trainium instances are only available in certain regions. You can check which regions support them [here](https://repost.aws/articles/ARmXIF-XS3RO27p0Pd1dVZXQ/what-regions-have-aws-inferentia-and-trainium-instances).

Also enable AWS FSx for Lustre CSI driver and deployment of FSx-L volume by setting `enable_aws_fsx_csi_driver` and `deploy_fsx_volume` variables in the file to `true`. The rest of the resources can be set to `false`, since they aren't used in this fine-tuning example.

Run the installation script to set up an EKS cluster with all required add-ons:

```bash
./install.sh
```

### Verify the resources

Check that your EKS cluster is running in the region you set earlier:

```bash
aws eks --region <region> describe-cluster --name trainium-inferentia
```

```bash
# Creates k8s config file to authenticate with EKS
aws eks --region <region> update-kubeconfig --name trainium-inferentia

kubectl get nodes # Output shows the EKS Managed Node group nodes
```

</CollapsibleContent>

## 2. Build the Docker Image

We'll use the [Optimum Neuron container image](https://huggingface.co/docs/optimum-neuron/en/containers) from HuggingFace as the base image for our Llama3 fine-tuning container. At the time of writing, this image includes Optimum Neuron version 0.0.25. Run the following commands from the root of the ai-on-eks repository:

**Note:** Make sure your AWS user has access to the ECR repository in your chosen region. The script will create the repo and push the image for you.

```bash
cd blueprints/training/llama-lora-finetuning-trn1
./build-container-image.sh
```
When prompted, enter the same region you used earlier.

## 3. Launch the Llama training job

Before starting the fine-tuning job, set up a Kubernetes Secret, a ConfigMap for the training script, and update the container image URL in the job spec.

To let the training script download the Llama 3 model from Hugging Face, you need your Hugging Face access token. You can manage and retrieve your access token under [settings](https://huggingface.co/docs/hub/en/security-tokens) on the HuggingFace website. Create a Kubernetes Secret for this access token by replacing the placeholder text `<HF_TOKEN>` with it.

```bash
kubectl create secret generic huggingface-secret --from-literal=HF_TOKEN=<HF_TOKEN>
```

Create the ConfigMap for the training script:

```bash
kubectl apply -f llama3-finetuning-script-configmap.yaml
```

**Note:** After launching the training script with the Kubernetes Job in lora-finetune-job.yaml, monitor the fine-tuning job by checking the log file in the /shared folder on FSx for Lustre. The fine-tuned model will be saved in a folder named llama3_tuned_model_<timestamp>. The script tests the model with sample prompts, saving results in a log file named llama3_finetuning_<timestamp>.out alongside the model folder. To view the fine-tuning logs and access the tuned model, use a utility pod to access the FSx for Lustre filesystem. Create this utility pod before starting the training job.

```bash
kubectl apply -f training-artifact-access-pod.yaml
```

Modify the lora-finetune-job.yaml file to enter the image URL for the container image. Replace the placeholder `<image-url>` text with the Docker image URL that's saved in the local file named `.ecr_repo_uri`. After saving the yaml file, launch the Kubernetes Job to run the script that fine-tunes the Llama3 model and tests the fine-tuned model using sample prompts:

```bash
kubectl apply -f lora-finetune-job.yaml
```

## 4. Verify fine-tuning

Check the job status:

```bash
kubectl get jobs
```

**Note:** If the container isn't scheduled, check Karpenter logs for errors. This might happen if the chosen availability zones (AZs) or subnets lack an available trn1.32xlarge EC2 instance. To fix this, update the local.azs field in the main.tf file, located at ai-on-eks/infra/base/terraform. Ensure the trainium-trn1 EC2NodeClass in the addons.tf file, also at ai-on-eks/infra/base/terraform, references the correct subnets for these AZs. Then, rerun install.sh from ai-on-eks/infra/trainium-inferentia to apply the changes via Terraform.

To monitor the log for the fine-tuning job, access the tuned model, or check the generated text-to-SQL outputs from the test run with the fine-tuned model, open a shell in the utility pod and navigate to the `/shared`  folder where these can be found.

```bash
kubectl exec -it training-artifact-access-pod -- /bin/bash

cd /shared

ls -l llama3_tuned_model* llama3_finetuning*
```

### Cleaning up

**Note:** Always run the cleanup steps to avoid extra AWS costs.

To remove the resources created by this solution, run these commands from the root of the ai-on-eks repository:

```bash
# Delete the Kubernetes resources:
cd blueprints/training/llama-lora-finetuning-trn1
kubectl delete -f lora-finetune-job.yaml
kubectl delete -f llama3-finetuning-script-configmap.yaml
kubectl delete secret huggingface-secret
kubectl delete -f training-artifact-access-pod.yaml
```

After making sure there are no other dependencies, delete the ECR repository and images:

```bash
aws ecr batch-delete-image --repository-name llm-finetune/llama-finetuning-trn --image-ids imageTag=feature-lora --region $(cat .eks_region)
# then delete the empty repository:
aws ecr delete-repository --repository-name llm-finetune/llama-finetuning-trn --region $(cat .eks_region)
# remove files created by the image builder script
rm .eks_region .ecr_repo_uri
```

Clean up the EKS cluster and related resources:

```bash
cd ../../../infra/trainium-inferentia/terraform
./cleanup.sh
```
