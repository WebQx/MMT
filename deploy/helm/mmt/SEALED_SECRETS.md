### Managing Secrets with Sealed Secrets

1. Create unsealed secret manifest (dry-run):
```
kubectl create secret generic transcripts-db \
  --from-literal=host=db.example \
  --from-literal=user=mmt \
  --from-literal=password='S3cret!' \
  --dry-run=client -o yaml > transcripts-db.yaml
```
2. Seal it:
```
kubeseal --format yaml < transcripts-db.yaml > transcripts-db-sealed.yaml
```
3. Commit the sealed file; NOT the plain one.
4. Apply in cluster (controller decrypts):
```
kubectl apply -f transcripts-db-sealed.yaml
```
5. Reference by name `transcripts-db` in the Helm chart (already used for retention job DB host).
