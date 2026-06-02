# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Distributed File Storage System.

## Components

- Namespace
- ConfigMap
- PersistentVolumeClaims
- Deployment
- NodePort Service
- Optional Ingress

## Structure

```text
k8s/
├── namespace.yaml
├── configmap.yaml
├── persistent-volume-claims.yaml
├── deployment.yaml
├── service.yaml
├── ingress.yaml
└── README.md