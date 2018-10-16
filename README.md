# Dictionary trainer

### Deploy in Kubernetes:

    kubectl create configmap dictrainer-config --from-file=docker/kubernetes/configmap/dictrainer-k8s.yml
    kubectl create configmap nginx-proxy-conf --from-file=docker/kubernetes/configmap/nginx-proxy.conf
    kubectl apply -f docker/kubernetes/templates/*.yml
    
    ...
    
### Rollout release:

    ./docker/build.sh && \
    ./docker/push.sh && \
    kubectl scale deployments/bot --replicas=0 && \
    kubectl scale deployments/bot --replicas=1
    
    
### Connect to http://dictrainer/
    kubectl port-forward service/nginx 8000:8000
    
    curl http://dictrainer/
    