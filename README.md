# RouteForge app
 # PDF ➜ Excel ➜ Route Optimization (https://mldevops.org)

app.mldevops.org hosted for uploading pdf file and extracting data into excel file and feeding excel sheet to Circuit app for routing shortest route.
Below are the steps for Building infrastructure for CI/CD setup.


1) Source → Build → Push (Jenkins stages / local equivalents)

Compute image tag

git rev-parse --short HEAD
Get-Date -Format "yyyyMMdd-HHmm"
# IMAGE_TAG = <sha>-<timestamp>


Login to ECR

aws sts get-caller-identity
aws ecr get-login-password --region us-east-2 |
  docker login --username AWS --password-stdin 577999460012.dkr.ecr.us-east-2.amazonaws.com


Build images

# backend
cd backend
docker build -t 577999460012.dkr.ecr.us-east-2.amazonaws.com/pdf-backend:${Env:IMAGE_TAG} .
cd ..

# frontend
cd frontend
docker build -t 577999460012.dkr.ecr.us-east-2.amazonaws.com/pdf-frontend:${Env:IMAGE_TAG} .
cd ..


Push images

docker push 577999460012.dkr.ecr.us-east-2.amazonaws.com/pdf-backend:${Env:IMAGE_TAG}
docker push 577999460012.dkr.ecr.us-east-2.amazonaws.com/pdf-frontend:${Env:IMAGE_TAG}

2) Connect kubectl to EKS and prepare namespace
aws eks update-kubeconfig --name mern-app-cluster --region us-east-2
kubectl create namespace pdfapp --dry-run=client -o yaml | kubectl apply -f -
kubectl get ns pdfapp

3) Deploy app with Helm (frontend + backend)
helm upgrade --install pdf-app charts/pdf-app -n pdfapp `
  --set images.frontend.repository=577999460012.dkr.ecr.us-east-2.amazonaws.com/pdf-frontend `
  --set images.frontend.tag=$Env:IMAGE_TAG `
  --set images.backend.repository=577999460012.dkr.ecr.us-east-2.amazonaws.com/pdf-backend `
  --set images.backend.tag=$Env:IMAGE_TAG `
  --wait --timeout 10m

kubectl -n pdfapp get deploy,svc,pods -o wide

4) Ingress + TLS

(Ingress controller already existed — reused it.)

Deploy ingress rules

helm upgrade --install pdfapp-ingress charts/pdfapp-ingress -n pdfapp --wait
kubectl -n pdfapp get ingress


(Cert-Manager was preinstalled; ClusterIssuer letsencrypt-prod was present.)
Check cert status

kubectl -n pdfapp get certificate,challenge,order
kubectl -n pdfapp describe certificate mldevops-org-tls


Route53

# Alias A record mldevops.org -> ALB/ingress address (already present)
# Verified:

kubectl -n pdfapp get ingress

5) Frontend API base (Vite)
# Production build uses:
Get-Content frontend/.env.production
# VITE_API_BASE=/api

6) Verifications

From cluster

kubectl -n pdfapp get svc backend-service -o wide
kubectl -n pdfapp get endpoints backend-service
kubectl -n pdfapp logs deploy/backend


Smoke tests

curl -si https://mldevops.org/
curl -si https://mldevops.org/api/health
# (Optionally) POST to extract:
curl -si -X POST https://mldevops.org/api/extract -F "file=@<some.pdf>"

7) Debugs you performed (and fixes)

404 from /api/extract (initial):

Confirmed browser hitting /api/extract.

Ensured ingress used regex + rewrite to strip /api:

helm upgrade --install pdfapp-ingress charts/pdfapp-ingress -n pdfapp --wait
kubectl -n pdfapp describe ingress ingress-pdfapp


503 from NGINX (no endpoints):

kubectl -n pdfapp get endpoints backend-service
kubectl -n pdfapp get pods -l app=backend --show-labels
kubectl -n pdfapp get svc backend-service -o yaml | Select-String selector
# Matched Service selectors with Pod labels, then:
kubectl -n pdfapp rollout restart deploy/backend
kubectl -n pdfapp get endpoints backend-service   # now shows pod IP:5000


Direct service checks (inside cluster):

kubectl -n pdfapp run tmp --image=curlimages/curl -it --rm --restart=Never -- \
  curl -si http://backend-service:5000/health

8) Final checks
kubectl -n pdfapp get all
kubectl -n pdfapp get ingress
kubectl -n pdfapp get certificate
# Browser: https://mldevops.org  → upload PDF → receives Excel


That’s the whole flow you executed—image build & push → EKS deploy via Helm → ingress/TLS with cert-manager → DNS with Route53 → debugged 404/503 via ingress rewrite and Service endpoints—until the app worked end-to-end.

