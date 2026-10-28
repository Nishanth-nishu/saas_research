# Research Rules (shared by every research task)

These rules apply to every agent and every file in this project.

## Evidence
1. Every important claim needs a direct source URL and an access date (use `2026-10-28` for today).
2. Only record a fact if you actually opened the page (WebFetch or browser) and saw it. If a fact comes only from a search-result snippet, label it `snippet-only`.
3. Label each claim as one of: `FACT` (observed on official/primary page), `VENDOR_CLAIM` (company's own marketing), `CUSTOMER_OPINION` (review, Reddit, forum), `HYPOTHESIS` (our interpretation).
4. Never invent: company names, people, emails, prices, customer counts, revenue, features, weaknesses, outcomes.
5. If a field cannot be verified, leave it blank and say what research is needed.
6. Record failed fetches (URL + reason) in your output's "Limitations" section. Do not use inaccessible pages as if read.
7. Pricing: capture plan name, price, currency, billing interval, usage limits, tax note, when shown.

## Access
- Public pages only. No logins, no bypassing paywalls, CAPTCHAs, rate limits or anti-bot measures.
- Do not scrape LinkedIn or Google Maps. A LinkedIn URL may be recorded only if it appeared in a search result or on the company's own site.
- No paid tools, no sign-ups.
- Never contact anyone: no emails, forms, messages, sign-ups, or chat widgets.

## People and contacts
- Record a person as decision-maker only if an official page (team/about page, press release, official profile) states their role.
- Emails: only record an email that is published on the company's own site or an authoritative directory. Never guess from patterns.
- Prefer business contact channels (info@, contact form, official phone) over personal ones. No personal phone numbers, home addresses, or sensitive data.

## Prospect CSV schema (exact header, in this order)
```
company_name,website,country,city_region,segment,niche,company_size,company_size_source,products_services,fit_evidence,fit_evidence_url,workflow_hypothesis,workflow_evidence,workflow_evidence_url,workflow_evidence_strength,evidence_date,value_signals,software_signals,software_source_url,decision_maker_name,decision_maker_role,decision_maker_source_url,linkedin_url,contact_page_url,public_email,public_email_source,public_phone,public_phone_source,contact_channel_type,buying_signals,buying_signal_url,buying_signal_date,verification_status,research_gaps,last_verified
```
Field notes:
- `segment`: one of `A_education`, `B_documents_logistics`, `C_agency_b2b_services`, `D_saas_ecommerce`.
- `workflow_evidence_strength`: `none` | `weak` (only industry inference) | `moderate` (public page shows the workflow exists, e.g. lead forms + multiple branches, or volume claims) | `strong` (job post / public statement showing manual work, or a stated bottleneck).
- `value_signals`: semicolon list of observed facts suggesting financial value, e.g. `5 branches; 2000+ students/year claimed (VENDOR_CLAIM)`.
- `software_signals`: tools visible on the site or in job posts (e.g. `Zoho CRM (job post)`, `WhatsApp chat widget (site)`, `Freshdesk (support portal subdomain)`).
- `contact_channel_type`: `verified_public_business_contact` | `public_professional_profile` | `official_contact_form` | `third_party_unverified` | `unknown`.
- `verification_status`: `verified` (exists, official site loaded) | `unverified`.
- Dates as YYYY-MM-DD. Leave unknowns blank. Use double quotes around any field containing commas.
