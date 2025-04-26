---
sidebar_label: Llama 3 Fine-tuning with LoRA
---
import CollapsibleContent from '../../../../src/components/CollapsibleContent';

:::warning
Deployment of ML models on EKS requires access to GPUs or Neuron instances. If your deployment isn't working, it's often due to missing access to these resources. Also, some deployment patterns rely on Karpenter autoscaling and static node groups; if nodes aren't initializing, check the logs for Karpenter or Node groups to resolve the issue.
:::

:::danger

Note: Use of this Llama 3 model is governed by the Meta license.
In order to download the model weights and tokenizer, please visit the [website](https://ai.meta.com/) and accept the license before requesting access.

:::

:::info

We are actively enhancing this blueprint to incorporate improvements in observability, logging, and scalability aspects.

:::

# Llama 3 fine-tuning on Trn1 with HuggingFace Optimum Neuron

This comprehensive guide walks you through the steps for fine-tuning the `Llama3-8B` language model using AWS Trainium (Trn1) EC2 instances. The fine-tuning process is facilitated by HuggingFace Optimum Neuron, a powerful library that simplifies the integration of Neuron into your training pipeline.

### What is Llama 3?

Llama 3 is a state-of-the-art large language model (LLM) designed for various natural language processing (NLP) tasks, including text generation, summarization, translation, question answering, and more. It's a powerful tool that can be fine-tuned for specific use cases.

#### AWS Trainium:
- **Optimized for Deep Learning**: AWS Trainium-based Trn1 instances are specifically designed for deep learning workloads. They offer high throughput and low latency, making them ideal for training large-scale models like Llama 3. Trainium chips provide significant performance improvements over traditional processors, accelerating training times.
- **Neuron SDK**: The AWS Neuron SDK is tailored to optimize your deep learning models for Trainium. It includes features like advanced compiler optimizations and support for mixed precision training, which can further accelerate your training workloads while maintaining accuracy.

## 1. Deploying the Solution

<CollapsibleContent header={<h2><span>Prerequisites</span></h2>}>
Before we begin, you will need to ensure you have all the prerequisites in place to make the deployment process smooth and hassle-free. You will need a machine from where you will be driving this solution deployment. You can use a local Mac/Windows machine or an Amazon EC2 machine. Ensure that you have Docker installed locally with storage above 100GB and that the image is created with x86 architecture.

Ensure that you have installed the following tools and have the required IAM permissions for the user/role you'll be using to deploy and run this solution.

* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
* [kubectl](https://Kubernetes.io/docs/tasks/tools/)
* [terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
* Git(Only for EC2 instance)
* Docker
* Python, pip, jq, unzip


**Clone the ai-on-eks repository**

After tackling the pre-requisites, let's get started by cloning the ai-on-eks github repository.

```bash
git clone https://github.com/awslabs/ai-on-eks.git
```

**Navigate to the trainium-inferentia directory.**

```bash
cd ai-on-eks/infra/trainium-inferentia
```

Set the region value within the `blueprint.tfvars` variables file under the `terraform` sub-folder to match your preference.

**NOTE:** Trainium instances are available in select regions, and the user can determine this list of regions using the commands outlined [here](https://repost.aws/articles/ARmXIF-XS3RO27p0Pd1dVZXQ/what-regions-have-aws-inferentia-and-trainium-instances) on re:Post.


Run the installation script to provision an EKS cluster with all the add-ons needed for the solution.

```bash
./install.sh
```

### Verify the resources

Verify the Amazon EKS Cluster after substituting the region value with the region you entered in the step above when setting up the infrastructure with terraform.

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

We'll build the docker image that will be used by the container to run Llama 3 fine-tuning. Execute the below commands after ensuring you are in the root folder of the ai-on-eks repository.

**NOTE:** Before running the docker image builder script, make sure the AWS user or principal used to run the script has proper access to the ECR repository in the specific region you selected earlier. The script will create a repo and push the image into it.

```bash
cd blueprints/training/llama-lora-finetuning-trn1
./build-container-image.sh
```
Enter the same region you provided in the above step, when prompted for it. After running this script, note the Docker image URL and tag that gets displayed at the end of the run. You will need this information for the next step.

## 3. Launch the Llama training job

Before launching the fine-tuning job, we'll need to set up a kubernetes Secret, a Configmap to mount the training script in the container, and update the container image URL in the Job specification.

In order for the training script to download the Llama3 model from HuggingFace, you need to provide your HuggingFace token. The access token can be found under Settings → Access Tokens on the Hugging Face website after you login to the HuggingFace website. This token will be served to the training container as a kubernetes Secret. For this we need to declare the secret by running the below create secret using kubectl.

```bash
kubectl create secret generic huggingface-secret --from-literal=HF_TOKEN=<HF_TOKEN>
```

The Job spec also uses a ConfigMap to be able to get the training script mounted into the training container. Run the apply command to create this ConfigMap.

```bash
kubectl apply -f llama3-finetuning-script-configmap.yaml
```

Update the container image value in the `lora-finetune-job.yaml` file with the Docker image URL and tag obtained from the previous step.

Once the corresponding pod is in 'Running' state, you can monitor the progress of the fine-tuning job by accessing the log file that's written to the FSx for Lustre(FSx-L) filesystem under the `/shared` folder. The fine-tuned model will also be saved in a subfolder named `llama3_tuned_model_<timestamp>`.

The training script runs a basic test at the end by passing in a few natural language prompts to compare how the fine-tuned model compares against the base model. This is captured in the output log from the training script and is made available along side the model artifacts folder using a similar naming scheme `llama3_finetuning_<timestamp>.out`.

For your convenience, you can get on an interactive shell of a utility pod to access the FSx-L filesystem to view the fine-tuning log and resulting fine-tuned model. Let's create this pod before launching the training job.


```bash
kubectl apply -f training-artifact-access-pod.yaml
```

We are now ready to apply the lora-finetune-job spec in the EKS cluster, which will launch our fine-tuning job.

```bash
kubectl apply -f lora-finetune-job.yaml
```

## 4. Verify fine-tuning

**Verify the Job Status:**

```bash
kubectl get jobs

```

**NOTE:** If the container fails to get scheduled, check the Karpenter logs for errors. Besides hitting resource limits or other common reasons, it's also possible that the infrastructure that was setup in the initial step through terraform ended up choosing a subnet whose AZ doesn't have trn1.32xlarge compute capacity. In such cases, you will need to update the `trainium-trn1` EC2NodeClass's subnet to one that is associated with an AZ that has capacity. You can find this EC2NodeClass definition in the `addons.tf` that gets copied under `infra/trainium-inferentia/terraform` folder. You'll need to re-run the `install.sh` script in that folder after making this update and then see if the pod gets scheduled in the new AZ/subnet by Karpenter.

Let's hop on an interactive shell of the utiliy pod to monitor the progress of the fine-tuning job and verify that the fine-tuned model gets written to the output folder, and the example prompts generate the corresponding SQL query.

```bash
kubectl exec -it training-artifact-access-pod -- /bin/bash

cd /shared

ls -l llama3*
```

### Cleaning up

**NOTE:** Please ensure to run the delete steps above and the cleanup script. This is even more important when running AWS accelerated EC2 compute instances for training/inference. Running those steps will allow for resources to get cleaned up afterwards in order to avoid additional cost in your AWS bill.

To remove the resources created using this solution, execute the below commands after ensuring you are in the root folder of the ai-on-eks repository.

```bash
# Delete the Kubernetes Resources:
cd blueprints/training/llama-lora-finetuning-trn1
kubectl delete -f lora-finetune-job.yaml
kubectl delete -f llama3-finetuning-script-configmap.yaml
kubectl delete secret huggingface-secret
kubectl delete -f training-artifact-access-pod.yaml
```

After ensuring there isn't any other dependencies on the below ECR repo and the images within it, delete the ECR repository

```bash

aws ecr batch-delete-image --repository-name llm-finetune/llama-finetuning-trn --image-ids imageTag=latest --region $(cat .eks_region)
#
# Then delete the empty repository:
aws ecr delete-repository --repository-name llm-finetune/llama-finetuning-trn --region $(cat .eks_region)
```

Clean Up the EKS Cluster and Associated Resources:

```bash
cd ../../../infra/trainium-inferentia/terraform
./cleanup.sh
```
