# One-time setup (about 10 minutes)

1. Create a free account at github.com, then click New repository.
   Name: printfluent-site. Choose **Private**. Create it.
2. On the new repo page click "uploading an existing file". Unzip this package on your PC and drag in
   EVERYTHING inside it (all folders, including the hidden .github folder). Click Commit changes.
   (If .github does not upload, use Add file > Create new file, name it .github/workflows/sync.yml and paste the file's text.)
3. Repo Settings > Secrets and variables > Actions > New repository secret.
   Name: ETSY_API_KEY   Value: your Etsy keystring.
4. Repo Settings > Actions > General > Workflow permissions: choose "Read and write permissions". Save.
5. Click the Actions tab > "Sync Etsy listings, build site, back up" > Run workflow.
   It takes a few minutes. Afterwards the repo holds all photos, videos and descriptions, and the run page
   has two downloads: "dist-ready-to-deploy" (drag into Cloudflare) and "backup-photos-videos-csv".
6. It then repeats every night by itself.

Optional, removes the manual deploy: in Cloudflare open lucky-rice-8819 > Settings > Build > Connect to Git,
choose this repo, build command `python3 build.py`, output folder `dist`.
