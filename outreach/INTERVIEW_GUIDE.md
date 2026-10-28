# Buyer Interview Guide (non-leading)

Purpose: learn how the workflow actually works today and whether it costs enough to pay for a fix.
Do **not** pitch during the first 20 minutes. Do not mention AI until the respondent describes the problem.
Length: 25–30 minutes. Record notes (with permission) in `data/interviews/<prospect_id>_<date>.md`.

## Rules (adapted from customer-development practice)
- Ask about **past behaviour** ("last time…"), not hypotheticals ("would you…").
- Ask for **numbers and examples**, not opinions.
- Never describe your solution until the end; then ask what would have to be true for them to pay.
- Silence is fine. Let them fill it.

## 1. Context (3 min)
1. What does your role cover day to day?
2. How big is the team that deals with [inquiries / documents / client reports / support tickets]?

## 2. The workflow, last instance (8 min)
3. Walk me through the last time a [new inquiry arrived / batch of invoices came in / monthly report was due / ticket came in]. What happened step by step?
4. Which tools did each step touch (sheets, WhatsApp, Tally, CRM, help desk…)?
5. Who did each step? How long did it take?
6. How often does this happen in a week or month? Is it seasonal?

## 3. Pain and cost (7 min)
7. What goes wrong most often? Tell me about the last time it went wrong.
8. What did that cost — lost student/customer, rework hours, penalty, delayed payment, client complaint?
9. How do you know it is happening (report, complaint, gut feel)?
10. If nothing changed for the next 12 months, what happens?

## 4. Past attempts and alternatives (5 min)
11. What have you already tried to fix this? (software, hiring, outsourcing, Zapier, an agency)
12. Why did that work or not work? What did it cost?
13. Is anyone currently evaluating a tool or vendor for this?

## 5. Buying process (5 min)
14. If you decided to fix this, who else would be involved? Who signs off on spend?
15. How did you buy the last software or service of a similar size? How long did it take?
16. Are there data or security requirements a vendor must meet (data location, access to Tally/CRM, NDAs)?
17. Is there a budget line this would come from?

## 6. Close (2 min)
18. Based on what you told me, would a 2–4 week paid pilot on [their specific workflow] be worth discussing? What would it need to show?
19. Who else do you know who deals with the same problem?
20. May I follow up with a short summary of what I heard?

## After the call — score immediately (0–3 each)
| Signal | 0 | 3 |
|---|---|---|
| Frequency | rare | daily |
| Quantified cost | none given | ₹/hours/lost deals stated |
| Past attempts | none | tried and paid for something |
| Budget owner identified | no | yes, on the call |
| Urgency | "someday" | active this quarter |
| Pilot interest | polite | asked for proposal/price |

≥12/18 = strong lead; record in `data/prospects.csv` → `outreach_status = pilot_proposed` only if a proposal is actually requested.
