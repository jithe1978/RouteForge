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

What I built & shipped (story in 60–90 seconds)

Containerized a 2-tier app (Vite/NGINX frontend + Flask/Gunicorn backend).

Pushed versioned images to Amazon ECR using a Git-driven IMAGE_TAG (<git-sha>-<timestamp>).

Deployed to an existing EKS cluster with Helm: one chart for the app (front + back), one chart for ingress.

Reused a cluster-wide ingress-nginx controller; terminated TLS with cert-manager + Let’s Encrypt; routed the domain via Route 53 A-alias.

Served frontend at https://mldevops.org and proxied API as https://mldevops.org/api/* → backend Service :5000 (regex + rewrite).

Chose ephemeral pod filesystem for generated XLSX (no EFS), knowing files get wiped on pod restart — acceptable for my use case.


############################################################################################################################################
What the Jenkins pipeline does (CI/CD)

Yes — the Jenkinsfile you used is both CI and CD.

CI (Continuous Integration):

Checks out code on every push to main.

Computes an immutable IMAGE_TAG.

Logs in to ECR.

Builds Docker images for frontend & backend.

Pushes images to ECR (artifact publishing).

CD (Continuous Delivery/Deployment):

Connects kubectl to EKS.

Ensures namespace exists.

Helm upgrade --install for the app chart, passing the new image tags → triggers rolling updates of Deployments.

Helm upgrade --install for the ingress chart.

Waits for readiness (--wait) and prints status.


##################################################################################################################################################################################################

PDF ➜ Excel ➜ Route Optimization (app.mldevops.org)

I just finished a small but end-to-end platform that takes a PDF, extracts tabular data into Excel, and feeds it to Circuit for shortest-route planning — all running on AWS EKS with a clean CI/CD story.

🧩 What I built

Frontend: Vite + NGINX (static)

Backend: Flask + Gunicorn (PDF → XLSX)

Containers & Registry: Docker → Amazon ECR (immutable tags: <git-sha>-<timestamp>)

Orchestration: Amazon EKS (reused existing cluster, nodes, VPC, subnets, security groups)

Deployments: Helm (app chart + separate ingress chart)

Ingress & TLS: ingress-nginx + cert-manager (Let’s Encrypt), Route 53 A-alias → ALB

Storage: Ephemeral pod filesystem (kept it simple; artifacts are transient by design)

CI/CD: Jenkins pipeline builds images, pushes to ECR, then helm upgrade --install for rollout

🔗 Routing model

https://app.mldevops.org → frontend

https://app.mldevops.org/api/* → backend :5000 (regex + rewrite via nginx annotations)

Frontend uses VITE_API_BASE=/api in .env.production so the browser stays decoupled from cluster internals.

🧪 Troubleshooting wins

404 on /api → fixed with use-regex: "true" + rewrite-target and path /api(/|$)(.*)

503 → validated Service Endpoints/labels; rolled out Deployments properly

ACME pending → verified ClusterIssuer + HTTP-01 against nginx ingress class

🧠 Why this design

Immutable tags for traceable, repeatable deploys

Split charts (app vs ingress) for reuse & cleaner change sets

TLS automation (Let’s Encrypt) for zero-touch cert renewals

Ephemeral storage to avoid EFS complexity (business-acceptable data lifetime)

📈 Next up

Post-deploy smoke test (/api/health) in Jenkins

HPA/requests/limits and basic observability (logs/metrics)

ECR retention policy to prune old images



#AWS #EKS #Kubernetes #Helm #Jenkins #Docker #Nginx #CertManager #LetsEncrypt #Route53 #Flask #Vite #DevOps #CICD #CloudEngineering
