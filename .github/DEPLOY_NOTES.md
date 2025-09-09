Deployment notes for backend and GitHub Pages

1) GitHub Pages (frontend)

- The gh-pages build workflow accepts an optional secret `PROD_BASE_URL`.
  If set, the workflow will pass `--dart-define=BASE_URL=<PROD_BASE_URL>` to `flutter build web`.
  This ensures the published web app points to your production API endpoint instead of `http://localhost:8000`.

  To set it:
  - Go to your repository Settings -> Secrets -> Actions -> New repository secret
  - Name: PROD_BASE_URL
  - Value: https://api.yourdomain.example

2) Backend CI / GHCR tagging

- The backend build workflows now ensure the GHCR repository path uses your GitHub repository owner (lowercase) to avoid Docker tag errors. They publish an image to `ghcr.io/<owner>/mmt-backend:<tag>`.

3) Helm / Kubernetes deploy

- The `deploy.yml` workflow intentionally does not configure cloud provider auth for you. You must add one of these options:
  a) OIDC / cloud provider action: use the appropriate provider action to request short-lived credentials and configure kubectl (recommended). Examples:
     - Google GKE: google-github-actions/get-gke-credentials
     - AWS EKS: aws-actions/configure-aws-credentials + aws eks update-kubeconfig
     - Azure AKS: azure/login + azure/aks-set-context
  b) KUBECONFIG secret: store a base64-encoded kubeconfig in a secret and write it to $HOME/.kube/config at runtime. This is less secure than OIDC.

- The workflow will fail early if no kube context is present to avoid attempting a blind deploy.

4) How to run a full deployment manually (example)

- Build and push backend image locally:
  docker build -t ghcr.io/<owner>/mmt-backend:mytag ./backend
  echo $GITHUB_TOKEN | docker login ghcr.io -u <github-username> --password-stdin
  docker push ghcr.io/<owner>/mmt-backend:mytag

- Update chart overrides (/tmp/overrides/values-override.yaml) to point to the image and run:
  helm upgrade --install mmt deploy/helm/mmt -f deploy/helm/mmt/values.yaml -f /tmp/overrides/values-override.yaml --namespace mmt --create-namespace

5) If you want the frontend to autodetect the API host at runtime

- Consider implementing a small lookup endpoint served from the Pages site or embedding the API base URL inside `index.html` at deploy time (more advanced). For now, use `PROD_BASE_URL` to bake the base URL into the web build.

If you choose GKE (Google Kubernetes Engine)

- Required repository Secrets (Actions -> Secrets -> New repository secret):
  - `GKE_PROJECT` - your Google Cloud project id
  - `GKE_CLUSTER` - the cluster name
  - `GKE_LOCATION` - cluster zone or region (e.g. us-central1)
  - `GKE_SA_KEY` - JSON key for a service account with the following roles:
    - roles/container.developer (or roles/container.admin for full permissions)
    - roles/storage.objectViewer (if pulling images from GCR/Artifact Registry)

- How to create the service account key:
  1. gcloud iam service-accounts create github-actions-deployer --display-name="GH Actions Deployer"
 2. gcloud projects add-iam-policy-binding <PROJECT_ID> --member="serviceAccount:github-actions-deployer@<PROJECT_ID>.iam.gserviceaccount.com" --role="roles/container.developer"
 3. gcloud projects add-iam-policy-binding <PROJECT_ID> --member="serviceAccount:github-actions-deployer@<PROJECT_ID>.iam.gserviceaccount.com" --role="roles/storage.objectViewer"
 4. gcloud iam service-accounts keys create key.json --iam-account=github-actions-deployer@<PROJECT_ID>.iam.gserviceaccount.com
 5. Copy the contents of `key.json` and paste into the `GKE_SA_KEY` repository secret.

- After adding these secrets the `deploy.yml` workflow will be able to authenticate to GKE for non-dev deployments.

If you want to provide an OpenAI API key to the backend

- Add a repository secret named `OPENAI_API_KEY` (Actions -> Secrets -> New repository secret). The secret value should be the raw API key string.

- During non-dev deployments the workflow will create a Kubernetes secret named `mmt-openai-secret` in the `mmt` namespace and mount it as the env var `OPENAI_API_KEY` inside the backend pod.

Note: The workflow expects `OPENAI_API_KEY` to be present as a repository secret; if missing the backend will be deployed without the key.
