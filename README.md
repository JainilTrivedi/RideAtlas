
# Guide

This document explains how to run the project stack locally (Kafka, Zookeeper, Neo4j, and the Kafka→Neo4j connector) and how to exercise the pipeline. It is written for a reader who wants to deploy and test the project end-to-end.

<!-- > The environment used by the automated grader is similar to this — these are the manual steps you can run locally to reproduce the behaviour. -->

# Prerequisites
- A Linux environment (Ubuntu 22.04 recommended) or WSL2 on Windows.
- minikube installed and available in PATH.
- helm and kubectl installed and available in PATH.
- python3 (>=3.8) and pip.

You will also need these Python packages (install with pip):

```bash
pip install confluent-kafka pyarrow
```

You may want a sample dataset (the grader uses a trip dataset):

```bash
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet
```

## Start the cluster

Start `minikube` (adjust settings to your machine):

```bash
minikube start --memory=6000 --cpus=6
```

Add the Neo4j Helm repo and update it:

```bash
helm repo add neo4j https://helm.neo4j.com/neo4j
helm repo update
```

## Useful kubectl commands

```bash
kubectl get pods
kubectl get services
kubectl logs deployment/kafka-deployment
kubectl delete -f <manifest>.yaml --ignore-not-found
```

## Step 1 — Deploy Zookeeper and Kafka

Apply the manifests to deploy Zookeeper and Kafka into the cluster:

```bash
kubectl apply -f ./zookeeper-setup.yaml
kubectl apply -f ./kafka-setup.yaml
```

Wait for pods to be `Running` and `Ready` before continuing.

## Step 2 — Deploy Neo4j

Install Neo4j with the provided `neo4j-values.yaml` to configure password/plugins:

```bash
helm install my-neo4j-release neo4j/neo4j -f neo4j-values.yaml
# If a service manifest is provided in the repo, apply it as well
kubectl apply -f neo4j-service.yaml
```

Confirm Neo4j pod(s) and service are up before proceeding.

## Step 3 — Deploy Kafka→Neo4j connector

Apply the connector deployment which reads from Kafka and writes to Neo4j:

```bash
kubectl apply -f kafka-neo4j-connector.yaml
```

The connector runs on port `8083` (see the connector service manifest).

## Step 4 — Run the data producer and test the pipeline

Forward relevant ports to access Neo4j and Kafka locally, then run the data producer to send messages into Kafka. Example:

```bash
kubectl port-forward svc/neo4j-service 7474:7474 7687:7687 &
kubectl port-forward svc/kafka-service 9092:9092 &
python3 data_producer.py
```

After the producer finishes, run the project tester script:

```bash
python3 tester.py
```

<!-- ## Notes and recommendations
- The manifests in this repo apply resources into the `default` namespace unless you add `metadata.namespace` or pass `-n <namespace>` to `kubectl`.
- For production-like Kafka/Zookeeper deployments, prefer `StatefulSet` and persistent volumes; the current manifests are intended for local/testing use.
- Add `readinessProbe` and `livenessProbe` for robust health handling in rolling updates.
- If you change service ports or names, update the connector environment variables (e.g., `CONNECT_BOOTSTRAP_SERVERS`, `NEO4J_HOST`, `NEO4J_AUTH`). -->

## Troubleshooting
- If pods are not starting: `kubectl describe pod <pod-name>` and `kubectl logs deployment/<deployment-name>`.
- If the connector cannot reach Neo4j or Kafka, verify the Service DNS names (e.g., `kafka-service:29092`, `neo4j-service:7687`) and that port-forwards are correct.
- If helm install fails, run `helm repo update` and inspect `helm status my-neo4j-release`.

## Cleanup

Remove deployed resources when finished:

```bash
kubectl delete -f kafka-neo4j-connector.yaml --ignore-not-found
kubectl delete -f kafka-setup.yaml --ignore-not-found
kubectl delete -f zookeeper-setup.yaml --ignore-not-found
helm uninstall my-neo4j-release || true
minikube stop
```
