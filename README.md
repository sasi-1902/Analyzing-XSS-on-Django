# Analyzing-XSS-on-Django
Analyze XSS Attacks on Modern Web Frameworks using Django


## Overview

This project explores how various Cross-Site Scripting (XSS) attacks can be performed on a Django-based blog application. It highlights common security misconfigurations, such as the misuse of template filters (like `|safe`) and client-side vulnerabilities, to demonstrate **Stored**, **Reflected**, and **DOM-Based XSS** in modern web frameworks.

---

## Tools & Environment

- **Operating System:** Kali Linux  
- **Framework:** Django  
- **Languages:** Python, HTML, JavaScript  
- **Security Tools:**
  - OWASP ZAP (Proxy Scan & Analysis)
  - Python HTTP Server (Attacker Listener)

---

## Features

- Simulated **Attacker-Victim** environment
- **Stored XSS** attack with cookie-stealing payload
- **Reflected XSS** using search field
- **DOM-Based XSS** via unsafe client-side script
- **ZAP Proxy Scan** report showing site weaknesses
- Secure-vs-Vulnerable implementation insights

---

## Setup Instructions

### 📁 Step 1: Extract or Navigate to Project Directory
```bash
cd ~/Webpen/django-blog\ app


/django-blog-app/
│
├── manage.py
├── db.sqlite3
├── requirements.txt
├── Procfile
├── LICENSE
│
├── blog/
├── core/
│   ├── views.py       # Includes search_posts logic
│   ├── urls.py
│
├── users/
│
├── templates/
│   ├── search.html          # Reflected XSS example
│   ├── domsearch.html       # DOM-Based XSS page
│   └── core/
│       └── post.html        # Stored XSS (|safe usage)
│
└── static/


