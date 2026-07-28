# Defense signatures

How to name what is standing in front of a site, and what each finding actually implies.
Read this when `probe_site.py` reports a vendor you want to understand, when it reports
nothing but requests still fail, or when you need to interpret a block page by hand.

## Contents

- [Reading the evidence](#reading-the-evidence)
- [Bot management vendors](#bot-management-vendors)
- [CAPTCHA types](#captcha-types)
- [Detection layers](#detection-layers)
- [Block page forensics](#block-page-forensics)

---

## Reading the evidence

The single most common analysis error is treating CDN presence as bot protection. Cloudflare
fronts a large share of the web; `cf-ray` on a response means the site uses a popular CDN and
nothing more. What distinguishes a CDN from an engaged bot manager is the appearance of
*state* — a cookie the vendor sets to track your session's trust score, or a challenge script.

| Signal class | Example | What it proves |
| --- | --- | --- |
| Passive edge marker | `cf-ray`, `x-served-by`, `x-amz-cf-id` | A CDN is in the path. Nothing about bot policy. |
| Active scoring cookie | `__cf_bm`, `_abck`, `datadome`, `_px3` | Bot management is running and scoring requests. |
| Challenge artifact | `/cdn-cgi/challenge-platform/`, `_Incapsula_Resource` | You were served an interstitial, not the content. |
| Clearance cookie | `cf_clearance` | A challenge was solved; sessions now carry a trust token. |

Judge difficulty from the second and third rows only.

---

## Bot management vendors

### Cloudflare
- **Passive**: `cf-ray`, `cf-cache-status`, `server: cloudflare`
- **Engaged**: `__cf_bm` cookie (Bot Management scoring), `cf_clearance` (challenge passed),
  `cf-mitigated` header, `/cdn-cgi/challenge-platform/` script
- **Behaviour**: tiered. Plain caching, then Bot Fight Mode, then Managed Challenge (Turnstile),
  then hard block. The same domain can serve all four depending on path and reputation.
- **Implication**: TLS and HTTP/2 fingerprint consistency matter more than User-Agent strings.

### Akamai Bot Manager
- **Passive**: `x-akamai-transformed`, `server: AkamaiGHost`
- **Engaged**: `_abck` (sensor cookie — its payload encodes session trust), `bm_sz`, `bm_sv`,
  `ak_bmsc`, `akamai-grn` on block pages
- **Behaviour**: collects browser telemetry client-side and validates it server-side. The
  `_abck` value itself indicates whether the sensor accepted the session.
- **Implication**: HTML-only clients rarely satisfy it, since it expects sensor POSTs.

### DataDome
- **Passive**: none — DataDome is not a CDN
- **Engaged**: `datadome` cookie, `x-datadome` / `x-dd-b` headers, `js.datadome.co`,
  `captcha.datadome.co`
- **Behaviour**: per-request ML scoring on IP reputation, headers, and behaviour. Serves a
  slider puzzle when uncertain rather than a hard block.
- **Implication**: datacenter IP ranges are scored harshly.

### HUMAN Security (formerly PerimeterX)
- **Engaged**: `_px3`, `_px2`, `_pxhd`, `_pxvid`, `_pxde` cookies, `px-cloud.net`, `/px/captcha`
- **Behaviour**: 403 with a "Please verify you are a human" interstitial.

### Kasada
- **Engaged**: `x-kpsdk-ct`, `x-kpsdk-cd`, `x-kpsdk-r` headers, `KP_UIDz` cookie
- **Behaviour**: deliberately unbranded. A bare 429 or 403 with a near-empty body and no vendor
  header anywhere is itself the signature — absence of evidence is the evidence.
- **Implication**: the hardest common tier. Treat as a strong signal to seek a sanctioned path.

### Imperva (Incapsula)
- **Engaged**: `incap_ses_*`, `visid_incap_*`, `nlbi_*` cookies, `x-iinfo`, `_Incapsula_Resource`

### AWS WAF Bot Control
- **Passive**: `x-amz-cf-id`, `x-amz-cf-pop` (plain CloudFront)
- **Engaged**: `aws-waf-token` cookie, `x-amzn-waf-action` header, `awswaf.com` challenge script
- **Behaviour**: rule-based more than ML-based; typically the mildest of the major vendors.

### F5 / BIG-IP ASM
- **Passive**: `BIGipServer*` (load balancing only)
- **Engaged**: `TS01*` / `TSPD_101` cookies, `/TSPD/` paths

---

## CAPTCHA types

Identify by script source and widget markup. The response field name is the most reliable tell
because it must appear in the form the site submits.

| Type | Script source | Widget marker | Response field |
| --- | --- | --- | --- |
| reCAPTCHA v2 | `google.com/recaptcha/api.js` | `.g-recaptcha` | `g-recaptcha-response` |
| reCAPTCHA v3 | `recaptcha/api.js?render=<key>` | none (invisible) | `g-recaptcha-response` |
| hCaptcha | `hcaptcha.com/1/api.js` | `.h-captcha` | `h-captcha-response` |
| Cloudflare Turnstile | `challenges.cloudflare.com/turnstile/v0/api.js` | `.cf-turnstile` | `cf-turnstile-response` |
| Arkose Labs (FunCaptcha) | `client-api.arkoselabs.com` | iframe | `fc-token` |
| GeeTest | path containing `/gt.js` | `.geetest_*` | `geetest_challenge` |

**What each implies for feasibility:**

- **Invisible scoring** (reCAPTCHA v3, Turnstile in passive mode) runs on every page view and
  gates nothing by itself. Content is often still reachable; the score feeds other decisions.
- **Interactive challenge** (reCAPTCHA v2, hCaptcha, Arkose, GeeTest) on the *content* path is a
  hard stop for automated collection. The site is asking for a human, explicitly.
- **Login/signup-only CAPTCHA** is irrelevant to public-content scraping. Check *where* the
  CAPTCHA appears before treating it as a blocker.

A CAPTCHA on the content path is a deliberate statement that the operator wants a human there.
Treat it as a routing decision — find a sanctioned path or drop the target — rather than an
obstacle to engineer around. Automating past it invites both a technical arms race you will
lose and a legal exposure you do not want.

---

## Detection layers

Modern vendors stack these. Understanding which layer is failing tells you what to change.

1. **Network / IP reputation** — datacenter ASNs score worse than residential. Symptom:
   blocked immediately and consistently, from every client, on the first request.
2. **TLS fingerprint (JA3/JA4)** — the cipher and extension ordering of your client's
   handshake. Symptom: `curl` and `requests` are blocked while a real browser is not, and
   changing User-Agent changes nothing. This is what `curl_cffi` exists to address.
3. **HTTP/2 framing** — SETTINGS frame order and pseudo-header order differ between real
   browsers and libraries. Symptom: same as TLS, and header spoofing does not help.
4. **Browser environment** — canvas, WebGL, fonts, `navigator.webdriver`, plugin counts.
   Symptom: headless browsers blocked while headed ones pass.
5. **Behavioural** — mouse movement, dwell time, request pacing and ordering. Symptom: the
   first requests succeed and blocking starts after a consistent volume or rhythm.

The consistency requirement is what defeats naive spoofing: a Chrome User-Agent on a Python TLS
fingerprint from a datacenter IP describes a machine that does not exist. Vendors detect the
contradiction, not any single value. Matching a coherent real client end to end is why
purpose-built libraries beat header spoofing.

---

## Block page forensics

When a request fails, classify before reacting:

| Status | Body | Likely cause |
| --- | --- | --- |
| 403 | vendor-branded interstitial | Bot management triggered |
| 403 | plain, no vendor markers | Auth or geo restriction, not bots |
| 429 | any | Rate limit — slow down; check `Retry-After` |
| 429/403 | near-empty, no headers | Kasada |
| 503 | "Checking your browser" | Cloudflare interstitial |
| 200 | shell with no content | Client-rendered, not blocked |

A 200 that contains nothing useful is the most misread result: it usually means the content
arrives by XHR, not that you were blocked. Check for an embedded JSON blob before reaching
for a browser.
