# Module 09: Social Engineering - Lab Guide

## Tools Used & Purpose

- **Social-Engineer Toolkit (SET)**: Deploying spear-phishing attack vectors, cloning target web pages for credential harvesting, and generating malicious media payloads.
- **Netcraft Anti-Phishing Extension**: Inspecting visited websites in real time to detect fraudulent clones, phishing domains, and hosting infrastructure.
- **PhishTank**: Verifying suspicious URLs and checking reported phishing domains against a global collaborative anti-phishing database.
- **ChatGPT / AI Prompts**: Generating persuasive phishing pretexts, professional business email compromise (BEC) lures, and writing-style mimicry.
- **OhPhish / GoPhish**: Enterprise phishing simulation frameworks used to execute controlled campaigns and measure employee awareness.

---

## 6. Detailed Hands-On Labs (Official CEHv13 Curriculum)

### Lab 1: Sniff Credentials using the Social-Engineer Toolkit (SET)

- <b>Lab Duration:</b> 20 Minutes \| <b>Required Privilege:</b> Root / Administrator
- <b>Target Environment:</b>
  - <i>Attacker VM:</i> Parrot Security (<code>10.10.1.13</code>)
  - <i>Victim VM:</i> Windows 11 (<code>10.10.1.11</code>)
  - <i>Target Web Application:</i> <code>http://www.moviescope.com</code>

#### Step-by-Step Practical Execution:

1. <b>Initialize Root Shell & Launch SET on Parrot Security:</b>
   ```bash
   # Switch to root user
   sudo su
   # Password: toor

   # Launch the Social-Engineer Toolkit
   setoolkit
   ```
2. <b>Navigate Attack Vectors in SET Interactive Menu:</b>
   - From the main menu, select option <code>1</code> (<b>Social-Engineering Attacks</b>).
   - From the next menu, select option <code>2</code> (<b>Website Attack Vectors</b>).
   - From the attack method menu, select option <code>3</code> (<b>Credential Harvester Attack Method</b>).
   - From the template/cloner menu, select option <code>2</code> (<b>Site Cloner</b>).
3. <b>Configure POST-Back IP and Target URL:</b>
   ```txt
   [-] IP address for the POST back in Harvester/Tabnabbing [10.10.1.13]: 10.10.1.13
   [-] Enter the url to clone: http://www.moviescope.com
   ```

   <p>
   <i>SET clones the full HTML, CSS, JavaScript, and asset structure of </i><i><code>www.moviescope.com</code></i><i> and binds a local Apache/Python web server to port 80 on </i><i><code>10.10.1.13</code></i><i>.</i>
   </p>
4. <b>Craft Phishing Lure Email:</b>
   - In Outlook/Webmail, compose an email to the victim:
     - <i>Subject:</i> <code>IMPORTANT: Moviescope Account Suspension Notice</code>
     - <i>Body:</i> <i>"Dear Customer, We regret to inform you that your MovieScope account has been temporarily suspended due to suspicious login activity. To avoid permanent cancellation, please log in below to confirm your details."</i>
     - <i>Hyperlink Text (Display As):</i> <code>www.moviescope.com/account-information</code>
     - <i>Actual Target URL (Web Address):</i> <code>http://10.10.1.13</code>
5. <b>Victim Execution on Windows 11:</b>
   - Victim logs into Windows 11 (<code>Admin / Pa$$w0rd</code>), opens Mozilla Firefox, and accesses the email.
   - Victim hovers over the link (observing <code>http://10.10.1.13</code>) and clicks it.
   - The browser renders an exact visual replica of MovieScope login page.
   - Victim enters credentials:
     - <b>Username:</b> <code>victim_user@moviescope.com</code>
     - <b>Password:</b> <code>Pa$$w0rd123!</code>
   - Victim clicks <b>Login</b>. The cloned site captures the POST parameters and automatically redirects the victim to the real <code>http://www.moviescope.com</code> to suppress suspicion.
6. <b>Harvested Credential Inspection on Parrot Terminal:</b>
   - In the Parrot Security terminal, SET captures and parses the incoming HTTP POST request in real-time:

   ```txt
   WE GOT A HIT! Printing the output:
   POSSIBLE USERNAME FIELD FOUND: Username=victim_user@moviescope.com
   POSSIBLE PASSWORD FIELD FOUND: Password=Pa$$w0rd123!

   WHEN FINISHED, HIT CONTROL-C TO GENERATE A REPORT.
   10.10.1.11 - - [12/Mar/2026 02:14:18] "POST /login.html HTTP/1.1" 302 -
   ```

---

### Lab 2: Detect Phishing Attacks using Netcraft Extension & Tools

- <b>Lab Duration:</b> 5 Minutes \| <b>Environment:</b> Windows 11 (<code>10.10.1.11</code>), Mozilla Firefox

#### Step-by-Step Practical Execution:

1. <b>Install Netcraft Browser Extension:</b>
   - In Firefox, navigate to <code>https://www.netcraft.com/apps-extensions</code>.
   - Scroll to <b>Browser Protection</b> and click <b>LEARN MORE</b>.
   - Click the <b>Firefox logo</b> and select <b>Add to Firefox</b> -> <b>Add</b> -> <b>Allow access to data for all websites</b>.
2. <b>Perform Site Inspection & Security Analysis:</b>
   - Navigate to <code>https://www.certifiedhacker.com</code>.
   - Click the <b>Netcraft Extension icon</b> in the browser toolbar.
   - Review immediate telemetry:
     - <i>Site Risk Rating:</i> Visual bar (0 to 10 scale) indicating likelihood of malicious or fraudulent activity.
     - <i>Country / Geolocation:</i> Physical hosting location of the web server.
     - <i>Web Server:</i> Detected HTTP server banner (e.g., Apache, Nginx, Cloudflare).
     - <i>Domain Registrar & Registration Date:</i> Age of domain (crucial metric; new domains \<30 days are high risk).
3. <b>Inspect Detailed Site Report:</b>
   - Click <b>Site Report</b> in the Netcraft popup to access comprehensive domain telemetry:
     - <i>SSL/TLS Certificate Validity & Issuer:</i> Validates whether certificate is DV (Domain Validated) or EV (Extended Validation) and checks for brand mismatches.
     - <i>Hosting History & IP Delegation:</i> Tracks changes in hosting providers and IP blocks over time.
4. <b>Phishing Interception & Blocking:</b>
   - When navigating to known phishing URLs or reported fraudulent domains, the Netcraft extension automatically intercepts the request, blocks page rendering, and displays a prominent warning screen:
     ```javascript
     [WARNING: PHISHING SITE BLOCKED BY NETCRAFT]
     The site you are attempting to visit has been reported as a phishing attack designed to steal financial credentials.
     ```

---

### Lab 3: Social Engineering using AI (ChatGPT Prompt Engineering & Writing Style Mimicry)

- <b>Lab Duration:</b> 15 Minutes \| <b>Environment:</b> Windows 11, Web Browser accessing <code>https://chatgpt.com</code>

#### Task 1: Crafting Phishing Emails via Prompt Engineering

1. <b>Customer Support Impersonation Prompt:</b>
   - <i>Prompt Provided to ChatGPT:</i>
     ```txt
     "Pose as a genuine Microsoft customer support executive with an imaginary name. Write a concise email stating that you have detected suspicious login activity on the user's account and urge them to reset their password on an urgent basis. Provide the reset link at [Fake Reset Link]."
     ```
   - <i>Generated Output Characteristics:</i> Grammatically flawless, authoritative tone, professional corporate signature, urgent call-to-action designed to bypass standard heuristic filters.
2. <b>IT Administrator Update Prompt:</b>
   - <i>Prompt Provided to ChatGPT:</i>
     ```txt
     "Write an email from a company's IT administrator to all employees letting them know that they need to install the latest mandatory security software. Provide a link where the employee can download the software. Let them know that all employees must complete the download by next Friday."
     ```
   - <i>Outcome Analysis:</i> Demonstrates how cybercriminals exploit compliance and authority to deploy trojanized executables under the guise of security patches.

#### Task 2: Writing Style Impersonation & Mimicry

1. <b>Synthesizing Messages Based on Corpus Analysis:</b>
   - <i>Prompt Provided to ChatGPT:</i>
     ```txt
     "Impersonate Sam's writing style from the conversations given below and create a message for John saying that his father suffered a massive heart attack today and he urgently needs financial assistance, urging John to transfer money immediately.

     Sample Conversations:
     Topic: Nature and Its Beauty
     John: Hey Sam, have you ever marveled at the beauty of nature?
     Sam: The celestial orb's descent into the horizon provides a resplendent spectacle, casting an ethereal kaleidoscope of hues upon the atmospheric canvas.
     John: I just love how the colors change.
     Sam: The chromatic metamorphosis, a transient masterpiece, orchestrates a symphony of spectral transitions, manifesting the ephemeral artistry inherent in the terrestrial firmament."
     ```
2. <b>Result Analysis & Threat Implications:</b>
   - ChatGPT adopts Sam's overly ornate, erudite vocabulary and sentence structure while delivering an urgent, emotionally distressing request for emergency money transfer.
   - <i>Takeaway:</i> Attackers can scrape an executive's public blog posts, emails, or LinkedIn articles, feed the corpus into an LLM, and produce spear-phishing lures that mirror the executive's writing style so precisely that colleagues fail to detect the fraud.

---

## 7. CEHv13 High-Frequency Exam Anchors & Review Checklist

### 7.1 Core Exam Distinctions Summary

- <b>Piggybacking vs. Tailgating:</b> Piggybacking involves the authorized user's active knowledge/consent (exploiting courtesy); tailgating is strictly unauthorized, covertly following without consent.
- <b>Pretexting vs. Reverse Social Engineering:</b> Pretexting is fabricating a persona to initiate contact with the victim; Reverse Social Engineering tricks the victim into initiating contact with the attacker (Sabotage -> Advertise -> Assist).
- <b>Phishing vs. Pharming:</b> Phishing uses deceptive links in messages; Pharming redirects valid traffic at the DNS or local hosts level without link interaction.
- <b>Spear Phishing vs. Whaling:</b> Spear phishing targets specific individuals or departments; Whaling specifically targets C-level executives, board members, or high-net-worth targets.
- <b>SPF vs. DKIM vs. DMARC:</b> SPF validates sender IP; DKIM cryptographically signs headers; DMARC dictates policy enforcement (<code>reject</code>/<code>quarantine</code>) and generates reports.
- <b>QRLJacking:</b> Intercepting and cloning session QR codes (WhatsApp Web/banking) to hijack user sessions upon mobile scanning.

### 7.2 Common Social Engineering Targets and Defense Strategies (Table 9.1 Mapping)

| Target Role | Common Attack Techniques | Defense Strategies |
| --- | --- | --- |
| <b>Front Desk / Receptionists</b> | Impersonation, pretexting, persuasion, intimidation, tailgating. | Enforce strict visitor badge/escort policies; train staff never to disclose internal extensions or schedules. |
| <b>Technical Support / Help Desk</b> | Vishing, pretexting, urgent emergency calls demanding password resets. | Strict call-back verification policies; require manager authorization before password resets. |
| <b>System Administrators</b> | Impersonation of executive, social engineering over phone/email. | Never disclose root/admin passwords; enforce hardware MFA (FIDO2) and out-of-band approvals. |
| <b>Finance / Accounting</b> | BEC (CEO Fraud), whaling, fake invoice redirection. | Dual authorization controls; mandatory telephone callback to established numbers for wire transfers. |
| <b>Mailroom Personnel</b> | Theft, interception, or forging of packages and mail. | Secure, locked mailrooms; monitored parcel intake; shredding discarded shipping labels. |
| <b>Janitorial / Cleaning Staff</b> | Impersonation, dumpster diving, eavesdropping. | Background checks, escorting third-party contractors, locking server rooms and phone closets at all times. |
